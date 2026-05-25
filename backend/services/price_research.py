"""
Market price research — uses eBay Sold Listings API.
Step 5 (cron) also calls this module.
"""
import httpx

from backend.config import settings
from backend.services.region import get_region


async def research_ebay_sold(keywords: str, limit: int = 20) -> dict:
    """
    Query eBay Finding API for recently sold listings.
    Returns avg sold price, price range, and sample items.
    Requires: EBAY_CLIENT_ID set in .env
    """
    base = (
        "https://svcs.sandbox.ebay.com" if settings.ebay_sandbox
        else "https://svcs.ebay.com"
    )
    r = get_region()
    url = f"{base}/services/search/FindingService/v1"
    params = {
        "OPERATION-NAME": "findCompletedItems",
        "SERVICE-VERSION": "1.13.0",
        "SECURITY-APPNAME": settings.ebay_client_id,
        "RESPONSE-DATA-FORMAT": "JSON",
        "GLOBAL-ID": f"EBAY-{r['country']}",  # e.g. EBAY-CA, EBAY-US
        "siteid": r["ebay_site_id"],            # e.g. 2 for Canada, 0 for US
        "keywords": keywords,
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "paginationInput.entriesPerPage": limit,
        "sortOrder": "EndTimeSoonest",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = (
        data.get("findCompletedItemsResponse", [{}])[0]
        .get("searchResult", [{}])[0]
        .get("item", [])
    )

    prices = []
    for item in items:
        try:
            price = float(item["sellingStatus"][0]["convertedCurrentPrice"][0]["__value__"])
            prices.append(price)
        except (KeyError, IndexError, ValueError):
            continue

    if not prices:
        return {"avg_sold": None, "min_price": None, "max_price": None, "sample_count": 0}

    return {
        "avg_sold": round(sum(prices) / len(prices), 2),
        "min_price": round(min(prices), 2),
        "max_price": round(max(prices), 2),
        "sample_count": len(prices),
    }


def recommend_price(
    market_data: dict,
    priority: str,
    platform: str,
    platform_fee_pct: float = 0.0,
    platform_fee_fixed: float = 0.0,
    shipping_cost: float = 0.0,
) -> dict:
    """
    Given market data and seller priority, suggest a list price
    and calculate expected net profit.
    """
    avg = market_data.get("avg_sold")
    if avg is None:
        return {"suggested_price": None, "net_profit": None, "reasoning": "No market data available"}

    multipliers = {"speed": 0.90, "balanced": 1.00, "price": 1.10}
    multiplier = multipliers.get(priority, 1.0)
    suggested = round(avg * multiplier, 2)

    platform_fee = round(suggested * platform_fee_pct + platform_fee_fixed, 2)
    net = round(suggested - platform_fee - shipping_cost, 2)

    priority_notes = {
        "speed": f"Priced 10% below market average (${avg}) for faster sale",
        "balanced": f"Priced at market average (${avg})",
        "price": f"Priced 10% above market average (${avg}) to maximize profit",
    }

    return {
        "suggested_price": suggested,
        "platform_fee": platform_fee,
        "shipping_cost": shipping_cost,
        "net_profit": net,
        "reasoning": priority_notes.get(priority, ""),
        "market_avg": avg,
        "market_range": f"${market_data.get('min_price')} – ${market_data.get('max_price')}",
    }
