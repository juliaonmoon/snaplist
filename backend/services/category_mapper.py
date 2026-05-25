"""
Map a SnapList listing to its best-matching Facebook Marketplace leaf category.

Uses Groq (same model as ai_analysis.py) given:
  - listing title, our category, keywords
  - the curated FB Marketplace taxonomy

Returns the exact FB leaf path so the Chrome extension can navigate the
category modal step-by-step. Never raises — returns None if no good match.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from backend.services.ai_analysis import _client, VISION_MODEL

TAXONOMY_PATH = Path(__file__).resolve().parent.parent / "data" / "fb_categories.json"


@lru_cache(maxsize=1)
def load_taxonomy() -> list[dict]:
    return json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))


def _taxonomy_summary(taxonomy: list[dict]) -> str:
    """Render leaf paths as ' > '-joined lines for the LLM prompt."""
    return "\n".join(f"- {' > '.join(c['path'])}" for c in taxonomy)


def _find_by_path(taxonomy: list[dict], path: list[str]) -> dict | None:
    """Match a returned path against the known taxonomy (exact, case-insensitive)."""
    if not path:
        return None
    lc_target = [p.strip().lower() for p in path]
    for entry in taxonomy:
        if [p.strip().lower() for p in entry["path"]] == lc_target:
            return entry
    # Fall back: match by leaf only (last element)
    leaf = lc_target[-1]
    for entry in taxonomy:
        if entry["path"][-1].strip().lower() == leaf:
            return entry
    return None


def _extract_json(text: str) -> dict | None:
    """Pull the first JSON object out of a model response, tolerating ```json fences."""
    if not text:
        return None
    # Strip ``` fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    # Or first balanced {...}
    first = re.search(r"\{[\s\S]*\}", text)
    if not first:
        return None
    try:
        return json.loads(first.group(0))
    except json.JSONDecodeError:
        return None


async def map_to_fb_category(
    title: str,
    our_category: str | None,
    keywords: list[str] | None,
) -> dict | None:
    """
    Returns a dict {path, leaf, confidence} matching the curated taxonomy, or None.
    Never raises.
    """
    taxonomy = load_taxonomy()
    kw = ", ".join((keywords or [])[:8])
    prompt = (
        "You map a second-hand-resale item to the SINGLE BEST Facebook Marketplace "
        "leaf category from the list below.\n\n"
        f"ITEM TITLE: {title}\n"
        f"OUR CATEGORY: {our_category or '(unknown)'}\n"
        f"KEYWORDS: {kw}\n\n"
        "ALLOWED FB CATEGORIES (you must pick one of these exact paths):\n"
        f"{_taxonomy_summary(taxonomy)}\n\n"
        "Respond with JSON ONLY, no prose, in this exact shape:\n"
        '{"path": ["Top","Middle","Leaf"], "confidence": 0.0}\n'
        "confidence is 0.0–1.0. If nothing fits well, use the path "
        '["Miscellaneous"] with low confidence.'
    )

    try:
        resp = _client.chat.completions.create(
            model=VISION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1,
        )
        content = resp.choices[0].message.content
    except Exception as e:
        print(f"[category_mapper] groq error: {type(e).__name__}: {e}")
        return None

    parsed = _extract_json(content or "")
    if not parsed or "path" not in parsed:
        print(f"[category_mapper] unparseable response: {content!r}")
        return None

    matched = _find_by_path(taxonomy, parsed["path"])
    if not matched:
        return None

    leaf = matched.get("leaf") or matched.get("name") or matched["path"][-1]
    return {
        "path": matched["path"],
        "leaf": leaf,
        "confidence": float(parsed.get("confidence", 0.5)),
    }


# Smoke test:  python -m backend.services.category_mapper
if __name__ == "__main__":
    import asyncio
    out = asyncio.run(map_to_fb_category(
        title="Vintage Eames-style Lounge Chair",
        our_category="Furniture",
        keywords=["eames", "lounge chair", "mid-century", "walnut"],
    ))
    print(json.dumps(out, indent=2))
