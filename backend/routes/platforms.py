from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Listing
from backend.services.region import get_region, platform_prefill_url

router = APIRouter(prefix="/platforms", tags=["platforms"])

PLATFORM_FEES = {
    "ebay":       {"percent": 0.13,  "fixed": 0.30},
    "etsy":       {"percent": 0.065, "fixed": 0.20},
    "facebook":   {"percent": 0.0,   "fixed": 0.0},
    "kijiji":     {"percent": 0.0,   "fixed": 0.0},
    "craigslist": {"percent": 0.0,   "fixed": 0.0},
    "gumtree":    {"percent": 0.0,   "fixed": 0.0},
}


class FeeEstimate(BaseModel):
    platform: str
    display_name: str
    list_price: float
    platform_fee: float
    shipping_cost: float
    net_profit: float
    currency: str


class FeeRequest(BaseModel):
    platforms: list[str]
    list_price: float
    shipping_cost: float = 0.0


@router.get("/available")
async def available_platforms():
    """Return the correct platform list for the seller's region."""
    r = get_region()
    platforms = [
        {"id": "facebook", "name": "Facebook Marketplace", "method": "browser", "shipping": True, "pickup": True},
        {"id": "ebay",     "name": f"eBay ({r['country']})", "method": "api",     "shipping": True, "pickup": False},
        {"id": "etsy",     "name": "Etsy",                   "method": "api",     "shipping": True, "pickup": False},
        {"id": "craigslist","name": "Craigslist",             "method": "browser", "shipping": False,"pickup": True},
    ]
    # Add country-specific classifieds
    classifieds = r["classifieds"]
    if classifieds["name"] not in ("Craigslist",):  # Craigslist already added
        platforms.insert(2, {
            "id": classifieds["name"].lower().replace(" ", "_"),
            "name": classifieds["name"],
            "method": "browser",
            "shipping": False,
            "pickup": True,
        })
    return {"region": r, "platforms": platforms}


@router.post("/fee-estimate", response_model=list[FeeEstimate])
async def estimate_fees(data: FeeRequest):
    """Calculate net profit for a given price across requested platforms."""
    r = get_region()
    results = []
    for platform in data.platforms:
        fee_config = PLATFORM_FEES.get(platform, {"percent": 0.0, "fixed": 0.0})
        platform_fee = round(data.list_price * fee_config["percent"] + fee_config["fixed"], 2)
        net = round(data.list_price - platform_fee - data.shipping_cost, 2)
        display_names = {
            "facebook": "Facebook Marketplace",
            "ebay": f"eBay {r['country']}",
            "kijiji": "Kijiji",
            "craigslist": "Craigslist",
            "gumtree": "Gumtree",
            "etsy": "Etsy",
        }
        results.append(FeeEstimate(
            platform=platform,
            display_name=display_names.get(platform, platform.capitalize()),
            list_price=data.list_price,
            platform_fee=platform_fee,
            shipping_cost=data.shipping_cost,
            net_profit=net,
            currency=r["currency"],
        ))
    return results


class PostResult(BaseModel):
    platform: str
    success: bool
    platform_listing_id: str | None = None
    url: str | None = None
    message: str | None = None


@router.post("/post/{listing_id}", response_model=list[PostResult])
async def post_to_platforms(
    listing_id: int,
    platforms: list[str],
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger posting to each requested platform.
    eBay and Etsy post automatically via API.
    Facebook, Kijiji, Craigslist, Gumtree return region-correct pre-fill URLs.
    """
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing_dict = {"title": listing.title, "description": listing.description}
    results = []

    for platform in platforms:
        if platform == "ebay":
            results.append(PostResult(platform="ebay", success=False, message="eBay API — add credentials to .env"))
        elif platform == "etsy":
            results.append(PostResult(platform="etsy", success=False, message="Etsy API — add credentials to .env"))
        else:
            url = platform_prefill_url(platform, listing_dict)
            results.append(PostResult(
                platform=platform,
                success=True,
                url=url,
                message="Open in browser — listing details pre-filled",
            ))
    return results
