"""
eBay Developer API integration — Step 3.
Handles OAuth token refresh and listing creation/management.
"""
import httpx

from backend.config import settings
from backend.services.region import get_region

EBAY_API_BASE = "https://api.sandbox.ebay.com" if settings.ebay_sandbox else "https://api.ebay.com"


async def get_oauth_token() -> str:
    """Exchange client credentials for an OAuth token (app-level)."""
    import base64
    credentials = base64.b64encode(
        f"{settings.ebay_client_id}:{settings.ebay_client_secret}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{EBAY_API_BASE}/identity/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def create_listing(listing_data: dict, oauth_token: str) -> dict:
    """
    Post a listing to eBay via the Sell Inventory API.
    Returns the eBay listing ID on success.
    Full implementation in Step 3 after API keys are provided.
    """
    headers = {
        "Authorization": f"Bearer {oauth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Inventory Item creation
    sku = f"snaplist-{listing_data['listing_id']}"
    inventory_payload = {
        "availability": {
            "shipToLocationAvailability": {"quantity": listing_data.get("quantity", 1)}
        },
        "condition": _map_condition(listing_data.get("condition", "good")),
        "product": {
            "title": listing_data["title"],
            "description": listing_data["description"],
            "imageUrls": listing_data.get("photo_urls", []),
        },
    }

    async with httpx.AsyncClient() as client:
        # Create/update inventory item
        resp = await client.put(
            f"{EBAY_API_BASE}/sell/inventory/v1/inventory_item/{sku}",
            headers=headers,
            json=inventory_payload,
        )
        if resp.status_code not in (200, 204):
            raise ValueError(f"eBay inventory error: {resp.text}")

        # Create offer
        r = get_region()
        offer_payload = {
            "sku": sku,
            "marketplaceId": r["ebay_marketplace_id"],
            "format": "FIXED_PRICE",
            "availableQuantity": listing_data.get("quantity", 1),
            "pricingSummary": {
                "price": {"value": str(listing_data["price"]), "currency": r["currency"]}
            },
            "listingDuration": "GTC",
            "merchantLocationKey": "default",
            "categoryId": listing_data.get("ebay_category_id", "99"),
        }
        offer_resp = await client.post(
            f"{EBAY_API_BASE}/sell/inventory/v1/offer",
            headers=headers,
            json=offer_payload,
        )
        offer_resp.raise_for_status()
        offer_id = offer_resp.json()["offerId"]

        # Publish offer
        publish_resp = await client.post(
            f"{EBAY_API_BASE}/sell/inventory/v1/offer/{offer_id}/publish",
            headers=headers,
        )
        publish_resp.raise_for_status()
        listing_id = publish_resp.json().get("listingId", "")

    return {"ebay_listing_id": listing_id, "sku": sku, "offer_id": offer_id}


async def check_sold_status(ebay_listing_id: str, oauth_token: str) -> bool:
    """Returns True if the eBay listing has sold."""
    headers = {"Authorization": f"Bearer {oauth_token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{EBAY_API_BASE}/sell/fulfillment/v1/order",
            headers=headers,
            params={"filter": f"orderfulfillmentstatus:{{NOT_STARTED|IN_PROGRESS}}"},
        )
        if resp.status_code != 200:
            return False
        orders = resp.json().get("orders", [])
        for order in orders:
            for item in order.get("lineItems", []):
                if item.get("listingId") == ebay_listing_id:
                    return True
    return False


def _map_condition(condition: str) -> str:
    mapping = {
        "new": "NEW",
        "like_new": "LIKE_NEW",
        "good": "GOOD",
        "fair": "ACCEPTABLE",
        "poor": "ACCEPTABLE",
    }
    return mapping.get(condition, "GOOD")
