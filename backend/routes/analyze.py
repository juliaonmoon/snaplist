"""
Photo upload + AI analysis endpoint.
POST /analyze/photo — upload image, get back AI-generated listing fields.
"""
import asyncio
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.services.ai_analysis import analyze_photo, generate_listing_content, research_product
from backend.services.ebay_scraper import fetch_sold_prices
from backend.services.product_identifier import identify_product

router = APIRouter(prefix="/analyze", tags=["analyze"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


class AnalysisResult(BaseModel):
    title: str
    category: str | None
    condition: str
    condition_description: str
    keywords: list[str]
    dimensions: str | None
    notes: str | None
    photo_path: str
    market: dict | None = None       # eBay sold-listings price distribution
    suggested_price: float | None = None  # convenience: market["suggested"] if present
    # Product identification + manufacturer research
    brand: str | None = None
    model: str | None = None
    identified_product: str | None = None
    identification_confidence: str | None = None
    identification_source: str | None = None  # groq_vision | claude_vision | google_lens
    seller_description: str | None = None  # ready-to-use, written in seller voice
    official_specs: str | None = None
    original_product_url: str | None = None
    msrp_original: float | None = None
    product_summary: str | None = None


@router.post("/photo", response_model=AnalysisResult)
async def analyze_item_photo(
    photo: UploadFile = File(...),
    priority: str = Form(default="balanced"),
    platform: str = Form(default="facebook"),
):
    """
    Upload a photo of an item. Claude Vision analyzes it and returns
    structured listing data: title, category, condition, keywords, dimensions.
    """
    if photo.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported image type: {photo.content_type}")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(photo.filename or "photo.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = upload_dir / filename

    content = await photo.read()
    with open(save_path, "wb") as f:
        f.write(content)

    try:
        analysis = await analyze_photo(str(save_path))
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=502, detail=f"Vision AI error: {e}")

    # ── Hybrid product identification: tries Google Lens → Claude Vision → falls back to Groq ──
    def _denull(v):
        if isinstance(v, str) and v.strip().lower() in ("null", "none", "n/a", ""):
            return None
        return v
    # Strip Groq's literal "null" strings before we layer any better identification on top.
    for k in ("brand", "model", "identified_product", "identification_confidence"):
        analysis[k] = _denull(analysis.get(k))

    try:
        better_id = await asyncio.wait_for(identify_product(str(save_path), analysis), timeout=25)
        if better_id and better_id.get("identification_confidence") in ("high", "medium"):
            analysis["brand"] = better_id.get("brand") or analysis.get("brand")
            analysis["model"] = better_id.get("model") or analysis.get("model")
            analysis["identified_product"] = better_id.get("identified_product") or analysis.get("identified_product")
            analysis["identification_confidence"] = better_id.get("identification_confidence")
            analysis["identification_source"] = better_id.get("source")
    except Exception:
        pass

    # ── Product research: if the vision step identified a brand/model, look up manufacturer specs ──
    try:
        research = await asyncio.wait_for(research_product(analysis), timeout=10)
    except Exception:
        research = {"official_specs": None, "original_product_url": None, "msrp_original": None, "summary": None}
    analysis["research"] = research

    # ── If we identified the product, rewrite the title to lead with it ──
    if analysis.get("identified_product") and analysis.get("identification_confidence") in ("high", "medium"):
        product = analysis["identified_product"]
        condition_word = {
            "new": "New", "like_new": "Like-new", "good": "Good condition",
            "fair": "Used", "poor": "For parts",
        }.get(analysis.get("condition", "good"), "Used")
        # Pre-pend the identified product; keep it concise for marketplace search.
        analysis["title"] = f"{product} — {condition_word}"[:80]

    # ── Build the seller-voice description on the backend ──
    desc_lines: list[str] = []
    if analysis.get("identified_product") and analysis.get("identification_confidence") in ("high", "medium"):
        desc_lines.append(f"Selling my {analysis['identified_product']}.")
    if research.get("summary"):
        desc_lines.append(research["summary"])
    cond_desc = analysis.get("condition_description")
    if cond_desc and cond_desc.lower() not in ("null", "none", ""):
        desc_lines.append(cond_desc)
    notes = analysis.get("notes")
    if notes and notes.lower() not in ("null", "none", ""):
        desc_lines.append(notes)
    if research.get("official_specs"):
        desc_lines.append(f"\nManufacturer specs:\n{research['official_specs']}")
    if research.get("msrp_original"):
        desc_lines.append(f"\nRetails new for ${research['msrp_original']}.")
    if research.get("original_product_url"):
        desc_lines.append(f"\nMore product info: {research['original_product_url']}")
    elif analysis.get("brand") and analysis.get("model"):
        from urllib.parse import quote
        q = quote(f"{analysis['brand']} {analysis['model']}")
        desc_lines.append(f"\nLook it up: https://www.google.com/search?q={q}")
    analysis["seller_description"] = "\n".join(desc_lines).strip()

    # ── Market price research (best-effort, never blocks the response > ~12s) ──
    market: dict = {"count": 0, "currency": "CAD"}
    title = analysis.get("title", "")
    keywords = analysis.get("keywords") or []
    query = " ".join([title, *keywords[:2]]).strip() or title
    if query:
        try:
            market = await asyncio.wait_for(fetch_sold_prices(query), timeout=12)
        except asyncio.TimeoutError:
            market = {"count": 0, "currency": "CAD", "error": "timeout"}
        except Exception as e:
            market = {"count": 0, "currency": "CAD", "error": f"{type(e).__name__}"}

    suggested_price = market.get("suggested") if market.get("count", 0) > 0 else None

    return AnalysisResult(
        title=title,
        category=analysis.get("category"),
        condition=analysis.get("condition", "good"),
        condition_description=analysis.get("condition_description", ""),
        keywords=keywords,
        dimensions=analysis.get("dimensions"),
        notes=analysis.get("notes"),
        photo_path=str(save_path),
        market=market,
        suggested_price=suggested_price,
        brand=analysis.get("brand"),
        model=analysis.get("model"),
        identified_product=analysis.get("identified_product"),
        identification_confidence=analysis.get("identification_confidence"),
        identification_source=analysis.get("identification_source"),
        official_specs=research.get("official_specs"),
        original_product_url=research.get("original_product_url"),
        msrp_original=research.get("msrp_original"),
        product_summary=research.get("summary"),
        seller_description=analysis.get("seller_description"),
    )
