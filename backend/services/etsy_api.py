"""Etsy API v3 integration — Step 3 (optional)."""
import httpx

from backend.config import settings

ETSY_API_BASE = "https://openapi.etsy.com/v3"


async def create_listing(listing_data: dict) -> dict:
    """Post a listing to Etsy. Requires ETSY_ACCESS_TOKEN."""
    headers = {
        "x-api-key": settings.etsy_api_key,
        "Authorization": f"Bearer {settings.etsy_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "title": listing_data["title"],
        "description": listing_data["description"],
        "price": listing_data["price"],
        "quantity": listing_data.get("quantity", 1),
        "who_made": "i_did",
        "when_made": "made_to_order",
        "is_supply": False,
        "state": "active",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{ETSY_API_BASE}/application/shops/{listing_data['shop_id']}/listings",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()
