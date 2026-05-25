"""
Daily monitoring logic shared between backend and cron/daily_monitor.py.
Called once per 24 hours by the cron job on DigitalOcean.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Listing, ListingStatus
from backend.models.inventory import NotificationLog, PriceHistory
from backend.services import ebay_api, price_research
from backend.services.notifications import send_daily_digest


async def run_daily_monitor(db: AsyncSession) -> dict:
    """
    For each active listing:
      1. Check eBay sold status
      2. Research current market prices
      3. Compare to seller's price and apply markdown rules
      4. Generate digest report
    Returns a summary dict for email dispatch.
    """
    result = await db.execute(
        select(Listing).where(Listing.status == ListingStatus.active)
    )
    listings = result.scalars().all()

    sold_items = []
    price_alerts = []
    markdown_suggestions = []

    for listing in listings:
        # 1. Check eBay sold status
        if listing.ebay_listing_id:
            try:
                token = await ebay_api.get_oauth_token()
                is_sold = await ebay_api.check_sold_status(listing.ebay_listing_id, token)
                if is_sold:
                    listing.status = ListingStatus.sold
                    listing.sold_at = datetime.now(timezone.utc)
                    sold_items.append({"title": listing.title, "platform": "ebay"})
                    continue
            except Exception:
                pass

        # 2. Market price research
        keywords = listing.title
        if listing.keywords:
            keywords = " ".join(listing.keywords[:3])
        market = await price_research.research_ebay_sold(keywords)

        # 3. Compare prices and apply markdown rules
        days_listed = 0
        if listing.listed_at:
            days_listed = (datetime.now(timezone.utc) - listing.listed_at).days

        for pl in listing.platform_listings:
            if pl.status != "active":
                continue

            current_price = pl.list_price
            avg_sold = market.get("avg_sold")

            # Price alert: more than 20% above market
            if avg_sold and current_price > avg_sold * 1.20:
                suggested = round(avg_sold * 1.05, 2)
                price_alerts.append({
                    "title": listing.title,
                    "platform": pl.platform,
                    "current_price": current_price,
                    "market_avg": avg_sold,
                    "suggested_price": suggested,
                    "listing_id": listing.id,
                    "platform_listing_id": pl.id,
                })

            # Markdown rule: days threshold reached
            md_days = listing.markdown_days or (listing.user and listing.user.default_markdown_days) or 14
            md_pct = listing.markdown_percent or (listing.user and listing.user.default_markdown_percent) or 10.0
            floor = listing.floor_price or (listing.user and listing.user.default_floor_price) or 0.0

            if days_listed >= md_days:
                new_price = round(current_price * (1 - md_pct / 100), 2)
                new_price = max(new_price, floor) if floor > 0 else new_price
                if new_price < current_price:
                    markdown_suggestions.append({
                        "title": listing.title,
                        "platform": pl.platform,
                        "current_price": current_price,
                        "suggested_price": new_price,
                        "days_listed": days_listed,
                        "listing_id": listing.id,
                        "platform_listing_id": pl.id,
                    })

    await db.commit()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sold_items": sold_items,
        "price_alerts": price_alerts,
        "markdown_suggestions": markdown_suggestions,
        "total_active": len(listings),
    }


def format_digest_email(report: dict) -> str:
    lines = ["Good morning! Here's your SnapList daily update:\n"]

    if report["sold_items"]:
        for item in report["sold_items"]:
            lines.append(f"✅ Sold: {item['title']} on {item['platform'].capitalize()}")
    else:
        lines.append("No new sales in the last 24 hours.")

    if report["price_alerts"]:
        lines.append("\n📉 Price Alerts:")
        for alert in report["price_alerts"]:
            lines.append(
                f"  • {alert['title']} (${alert['current_price']}) — market avg ${alert['market_avg']}. "
                f"Suggest dropping to ${alert['suggested_price']}."
            )

    if report["markdown_suggestions"]:
        lines.append("\n⏰ Markdown Rules Triggered:")
        for md in report["markdown_suggestions"]:
            lines.append(
                f"  • {md['title']} — unsold {md['days_listed']} days. "
                f"Drop from ${md['current_price']} → ${md['suggested_price']}?"
            )

    lines.append(f"\n{report['total_active']} active listing(s) total.")
    return "\n".join(lines)
