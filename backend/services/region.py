"""
Region-aware platform configuration.
Drives correct URLs, marketplace IDs, and currency per seller location.
"""
from backend.config import settings

# eBay marketplace IDs by country code
EBAY_MARKETPLACE = {
    "CA": "EBAY_CA",
    "US": "EBAY_US",
    "UK": "EBAY_GB",
    "AU": "EBAY_AU",
    "DE": "EBAY_DE",
    "FR": "EBAY_FR",
}

# eBay site IDs for the Finding API (legacy, needed for sold-listings search)
EBAY_SITE_ID = {
    "CA": "2",
    "US": "0",
    "UK": "3",
    "AU": "15",
    "DE": "77",
    "FR": "71",
}

# eBay base domains for browse links
EBAY_DOMAIN = {
    "CA": "ebay.ca",
    "US": "ebay.com",
    "UK": "ebay.co.uk",
    "AU": "ebay.com.au",
    "DE": "ebay.de",
    "FR": "ebay.fr",
}

# Kijiji exists only in Canada; equivalent classifieds elsewhere
CLASSIFIEDS_PLATFORM = {
    "CA": {"name": "Kijiji", "url": "kijiji.ca"},
    "US": {"name": "Craigslist", "url": "craigslist.org"},
    "UK": {"name": "Gumtree", "url": "gumtree.com"},
    "AU": {"name": "Gumtree AU", "url": "gumtree.com.au"},
    "DE": {"name": "eBay Kleinanzeigen", "url": "kleinanzeigen.de"},
    "FR": {"name": "Leboncoin", "url": "leboncoin.fr"},
}

CURRENCY_SYMBOL = {
    "CAD": "C$", "USD": "$", "GBP": "£", "AUD": "A$", "EUR": "€",
}


def get_region():
    country = settings.country.upper()
    return {
        "country": country,
        "currency": settings.currency,
        "currency_symbol": CURRENCY_SYMBOL.get(settings.currency, "$"),
        "ebay_marketplace_id": EBAY_MARKETPLACE.get(country, "EBAY_US"),
        "ebay_site_id": EBAY_SITE_ID.get(country, "0"),
        "ebay_domain": EBAY_DOMAIN.get(country, "ebay.com"),
        "classifieds": CLASSIFIEDS_PLATFORM.get(country, {"name": "Craigslist", "url": "craigslist.org"}),
        "city": settings.city,
        "region": settings.region,
    }


def platform_prefill_url(platform: str, listing: dict) -> str:
    """
    Generate a pre-fill URL for browser-based platforms.
    Opens the platform's new listing page with fields populated as query params
    where supported, or returns the new listing page directly.
    """
    r = get_region()
    title = listing.get("title", "")
    price = listing.get("price", "")
    description = listing.get("description", "")

    if platform == "facebook":
        # Facebook Marketplace new listing (location inferred from user's FB account)
        return "https://www.facebook.com/marketplace/create/item"

    if platform == "kijiji" and r["country"] == "CA":
        return "https://www.kijiji.ca/p-post-ad.html"

    if platform == "craigslist":
        # Craigslist subdomain is city-based
        city_slug = r["city"].lower().replace(" ", "")
        return f"https://{city_slug}.craigslist.org/post"

    if platform == "gumtree" and r["country"] in ("UK", "AU"):
        domain = "gumtree.com" if r["country"] == "UK" else "gumtree.com.au"
        return f"https://www.{domain}/sell"

    if platform == "etsy":
        return "https://www.etsy.com/sell"

    return ""
