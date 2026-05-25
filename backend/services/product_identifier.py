"""
Hybrid product identification for SnapList.

Tries identifiers in order, returning the first high-confidence hit:

  1. SerpAPI Google Lens     — real reverse-image search, 100/mo free.
  2. Claude Vision (Sonnet)  — strong visual product memory, pay-per-photo.
  3. Groq vision (already)   — already runs as the primary analysis step.

Each tier requires its own API key. If a key is missing the tier is skipped,
so the chain degrades gracefully back to whatever Groq returned.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Optional

import httpx

from backend.config import settings


# ───────────────────────── photo-hash cache ─────────────────────────
# Same photo → same identification result. We hash the file bytes (sha256)
# and persist results to a tiny JSON file so a backend restart doesn't lose them.

_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "id_cache.json"


def _photo_hash(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _load_cache() -> dict:
    if not _CACHE_PATH.exists():
        return {}
    try:
        return json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


# ───────────────────────── helpers ─────────────────────────

_BRAND_HINTS = (
    "ikea", "herman miller", "eames", "apple", "macbook", "iphone", "ipad",
    "sony", "samsung", "lg", "bosch", "kitchenaid", "le creuset", "vitamix",
    "dyson", "lego", "nikon", "canon", "nintendo", "playstation", "xbox",
    "weber", "yeti", "patagonia", "north face", "lululemon", "nike", "adidas",
)


def _looks_like_a_product(text: str) -> bool:
    """Heuristic: does this look like a real product title (brand + model)?"""
    t = text.lower()
    return any(b in t for b in _BRAND_HINTS) or bool(re.search(r"\b[A-ZÄÖÅ]{3,}\b", text))


def _empty() -> dict:
    return {
        "brand": None,
        "model": None,
        "identified_product": None,
        "identification_confidence": "none",
        "source": None,
    }


def _clean(v):
    """Groq often returns the literal string 'null' instead of JSON null. Normalize."""
    if v is None:
        return None
    if isinstance(v, str) and v.strip().lower() in ("null", "none", "n/a", ""):
        return None
    return v


# ───────────────────────── tier 1: SerpAPI Google Lens ─────────────────────────

async def _upload_to_public_host(image_path: str) -> Optional[str]:
    """Upload the photo anonymously to get a public URL SerpAPI can reach.

    Uses catbox.moe — no API key required, returns the public URL as plain text.
    """
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        files = {"fileToUpload": (Path(image_path).name, data, "image/jpeg")}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files=files,
            )
            if r.status_code == 200:
                url = r.text.strip()
                if url.startswith("http"):
                    return url
    except Exception:
        return None
    return None


def _parse_lens_results(data: dict) -> dict:
    """Pick the best product match out of SerpAPI's google_lens response."""
    matches = data.get("visual_matches") or data.get("knowledge_graph") or []
    if isinstance(matches, dict):
        matches = [matches]

    if not matches:
        return {
            "brand": None, "model": None, "identified_product": None,
            "identification_confidence": "none", "source": "google_lens",
        }

    # Heuristic: prefer matches whose title contains a known brand hint.
    best = None
    for m in matches[:10]:
        title = (m.get("title") or "").strip()
        if not title:
            continue
        if _looks_like_a_product(title):
            best = m
            break
    if not best:
        best = matches[0]

    title = (best.get("title") or "").strip()
    source = best.get("source") or best.get("link") or None

    # Try to split "PRODUCT - BRAND" or "BRAND PRODUCT" out of the title.
    brand, model = None, None
    if " - " in title:
        head, _, tail = title.rpartition(" - ")
        # If the tail looks brand-like (short, capitalized), treat it as brand.
        if 2 <= len(tail) <= 30 and tail.replace(" ", "").isalpha():
            brand = tail.strip()
            model = head.strip()
    if not brand:
        # First word might be the brand (IKEA, Apple, Sony...)
        first = title.split(" ", 1)[0] if title else ""
        if first and first.upper() == first and len(first) >= 3:
            brand = first
            model = title[len(first):].strip(" -")

    return {
        "brand": brand,
        "model": model,
        "identified_product": title or None,
        "identification_confidence": "high" if title and _looks_like_a_product(title) else "medium" if title else "none",
        "source": "google_lens",
        "match_url": source,
    }


async def identify_via_google_lens(image_path: str) -> Optional[dict]:
    """Run a Google Lens reverse-image search via SerpAPI."""
    if not settings.serpapi_key:
        return None

    public_url = await _upload_to_public_host(image_path)
    if not public_url:
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                "https://serpapi.com/search.json",
                params={
                    "engine": "google_lens",
                    "url": public_url,
                    "api_key": settings.serpapi_key,
                },
            )
            r.raise_for_status()
            data = json.loads(r.content.decode("utf-8"))
    except Exception:
        return None

    return _parse_lens_results(data)


# ───────────────────────── tier 2: Claude Vision ─────────────────────────

CLAUDE_IDENTIFY_PROMPT = """You are a product identification expert. Look at this photo and identify the specific product if you recognize it (brand, model name, SKU when visible). Famous designer/manufacturer items (IKEA, Herman Miller, Eames, Apple, KitchenAid, Le Creuset, etc.) should be recognizable from design alone.

Return ONLY a JSON object with these fields:
{
  "brand": "manufacturer if recognizable, else null",
  "model": "specific product name/SKU if recognizable, else null",
  "identified_product": "full name combining brand+model (e.g. 'IKEA ÖRFJÄLL swivel chair'), else null",
  "identification_confidence": "high | medium | low | none",
  "reasoning": "one sentence on what visual cues you used"
}

Be honest. If you can't identify it specifically, return nulls and confidence 'none'. Do not guess."""


async def identify_via_claude(image_path: str) -> Optional[dict]:
    """Ask Claude Sonnet to identify the product visually."""
    if not settings.anthropic_api_key:
        return None

    path = Path(image_path)
    if not path.exists():
        return None

    suffix = path.suffix.lower()
    media_type = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
    }.get(suffix, "image/jpeg")

    with open(path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 512,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": CLAUDE_IDENTIFY_PROMPT},
            ],
        }],
    }

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            r = await client.post("https://api.anthropic.com/v1/messages", json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return None

    text = (data.get("content") or [{}])[0].get("text", "").strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        result = json.loads(text.strip())
    except json.JSONDecodeError:
        return None

    result["source"] = "claude_vision"
    return result


# ───────────────────────── orchestrator ─────────────────────────

async def identify_product(image_path: str, groq_result: dict) -> dict:
    """Run identifiers in order, return the best hit.

    Results are cached per-photo (sha256 of file bytes) so the same image is
    never sent to a paid API twice.
    """
    floor = {
        "brand": _clean(groq_result.get("brand")),
        "model": _clean(groq_result.get("model")),
        "identified_product": _clean(groq_result.get("identified_product")),
        "identification_confidence": _clean(groq_result.get("identification_confidence")) or "none",
        "source": "groq_vision" if _clean(groq_result.get("identified_product")) else None,
    }

    # Cache check — same photo bytes → same result, no re-search.
    try:
        photo_id = _photo_hash(image_path)
        cache = _load_cache()
        if photo_id in cache:
            cached = cache[photo_id]
            cached["from_cache"] = True
            return cached
    except Exception:
        photo_id = None
        cache = {}

    # Tier 1: Google Lens
    lens = await identify_via_google_lens(image_path)
    if lens and lens.get("identification_confidence") in ("high", "medium"):
        if photo_id:
            cache[photo_id] = lens
            _save_cache(cache)
        return lens

    # Tier 2: Claude Vision
    claude = await identify_via_claude(image_path)
    if claude and claude.get("identification_confidence") in ("high", "medium"):
        if photo_id:
            cache[photo_id] = claude
            _save_cache(cache)
        return claude

    # Tier 3 (already-baseline): Groq — only cache if the baseline actually identified something
    if photo_id and floor.get("identified_product"):
        cache[photo_id] = floor
        _save_cache(cache)
    return floor
