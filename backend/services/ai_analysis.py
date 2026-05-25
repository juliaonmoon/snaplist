"""
Groq vision integration — free tier, no credit card required.
Get your key at console.groq.com → API Keys.
Uses meta-llama/llama-4-scout-17b-16e-instruct for vision analysis.
"""
import base64
import json
from pathlib import Path

from groq import Groq

from backend.config import settings

_client = Groq(api_key=settings.groq_api_key)
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

ANALYSIS_PROMPT = """You are helping a real person — Julia — write a marketplace listing for an item she is selling. Everything you write will be shown to potential buyers AS HER OWN WORDS. Write in first-person, casual, friendly seller voice. Never sound like an AI analyzing a photo (no "appears to be", "seem to be", "the chair has"). Talk to the buyer.

Return a JSON object with exactly these fields:

{
  "title": "Clear, searchable item title (max 80 chars). No brand-name guessing — keep it generic if unsure.",
  "category": "Best matching resale category (e.g. Electronics, Furniture, Clothing, Tools, Sports, etc.)",
  "condition": "one of: new, like_new, good, fair, poor",
  "condition_description": "1-2 sentences in Julia's voice telling the buyer about wear/marks honestly. Example: 'There are a couple of small stains on the seat — you can see them in the photos. The frame and wheels are still in great shape.' NOT 'The chair appears to be in good condition.'",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "dimensions": "Estimated dimensions or size if identifiable, otherwise null",
  "notes": "1-2 short sentences in Julia's voice with anything else a buyer would want to know (smoke-free home, pickup details, etc.). Friendly and brief. null if nothing meaningful to add.",
  "brand": "Identified manufacturer/brand if recognizable (e.g. IKEA, Herman Miller, Apple), otherwise null",
  "model": "Identified product model/name if recognizable (e.g. POÄNG, Eames Lounge, MacBook Pro 14\\"), otherwise null",
  "identified_product": "Full product identification combining brand and model (e.g. 'IKEA POÄNG armchair'), or null if not identifiable",
  "identification_confidence": "one of: high, medium, low, none — how confident you are in the brand/model identification"
}

For identification: look at distinctive design cues, labels, logos, badges, tags, screws/joinery patterns, font choices on labels, etc. Be conservative — if you're not sure, say null and set confidence to "none". Famous designer/brand items (IKEA, Herman Miller, Eames, Le Creuset, KitchenAid, Apple, Sony, etc.) should be recognizable from design alone.

Be honest about condition. Return only valid JSON — no markdown fences, no extra text."""


PRODUCT_RESEARCH_PROMPT = """You are a product research assistant. Given an identified product, return a JSON object with the manufacturer's original specifications and a link to the official product page.

Product: {product}
Brand: {brand}
Model: {model}

Return JSON with exactly these fields:
{{
  "official_specs": "Concise bullet list of the manufacturer's key specs (dimensions, materials, weight, capacity, features). Use newlines between bullets. If you don't know, return null.",
  "original_product_url": "URL to the official manufacturer product page if you know it with high confidence (e.g. https://www.ikea.com/.../poang...). Return null if you're not certain — do NOT guess URLs.",
  "msrp_original": "Original retail price (number only, in USD or null if unknown)",
  "summary": "One-sentence summary of what this product is and what it's known for."
}}

Only include URLs you are highly confident exist. A null URL is much better than a broken link. Return only valid JSON — no markdown fences."""


async def analyze_photo(image_path: str) -> dict:
    """Send a photo to Groq vision and return structured item analysis."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    suffix = path.suffix.lower()
    media_type_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    media_type = media_type_map.get(suffix, "image/jpeg")

    with open(path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    response = _client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{image_data}"},
                    },
                    {"type": "text", "text": ANALYSIS_PROMPT},
                ],
            }
        ],
        max_tokens=1024,
        temperature=0.2,
    )

    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


async def research_product(analysis: dict) -> dict:
    """If the vision step identified a brand/model, look up manufacturer specs and URL."""
    if not analysis.get("identified_product") or analysis.get("identification_confidence") in (None, "none", "low"):
        return {"official_specs": None, "original_product_url": None, "msrp_original": None, "summary": None}

    prompt = PRODUCT_RESEARCH_PROMPT.format(
        product=analysis.get("identified_product", ""),
        brand=analysis.get("brand", ""),
        model=analysis.get("model", ""),
    )
    response = _client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.1,
    )
    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {"official_specs": None, "original_product_url": None, "msrp_original": None, "summary": None}


async def generate_listing_content(analysis: dict, platform: str, priority: str) -> dict:
    """Generate a platform-optimized title and description from the AI analysis."""
    platform_limits = {
        "ebay": 80, "facebook": 100, "kijiji": 100, "craigslist": 70, "etsy": 140,
    }
    title_limit = platform_limits.get(platform, 80)
    priority_instruction = {
        "speed": "Focus on quick sale appeal — emphasize value and convenience.",
        "price": "Emphasize quality and features to justify a higher price point.",
        "balanced": "Balance value and quality.",
    }.get(priority, "")

    research = analysis.get("research") or {}
    specs_block = ""
    if research.get("official_specs"):
        specs_block = f"\n\nOfficial manufacturer specs:\n{research['official_specs']}"
    url_block = ""
    if research.get("original_product_url"):
        url_block = f"\n\nOriginal product page: {research['original_product_url']}"
    msrp_block = ""
    if research.get("msrp_original"):
        msrp_block = f"\n\nOriginal retail price: ${research['msrp_original']}"

    prompt = f"""Generate a {platform} resale listing for this item.

Item details:
{json.dumps({k: v for k, v in analysis.items() if k != 'research'}, indent=2)}
{specs_block}{url_block}{msrp_block}

Requirements:
- Title: max {title_limit} characters, keyword-rich for search. If a brand/model was identified, include it.
- Description: honest, clear, 4-6 sentences. Structure:
  1. What it is (use the identified product name if known)
  2. Original manufacturer specs (if provided above)
  3. Condition notes (be honest about wear)
  4. Pickup/shipping note
  5. If an original product URL was provided, end with "Original product info: <url>"
- {priority_instruction}

Return only valid JSON: {{"title": "...", "description": "..."}}"""

    response = _client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.3,
    )
    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
