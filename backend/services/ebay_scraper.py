"""
eBay sold-listings price scraper (no API key required).

Hits eBay CA's public sold-listings search page, extracts realized prices,
and returns a price distribution. Used by the AI analysis flow to suggest
a competitive starting price based on what items actually sold for.

Best-effort — eBay can rate-limit or change markup at any time. Always
returns a dict; never raises. If results can't be parsed, count == 0.
"""
from __future__ import annotations

import asyncio
import re
import statistics
from urllib.parse import quote_plus

import httpx

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# Match a span class="s-item__price" and capture its text content.
# eBay sometimes nests an inner <span> for currency code — we strip tags after.
_PRICE_BLOCK_RE = re.compile(
    r'<span[^>]*class="[^"]*s-item__price[^"]*"[^>]*>(.*?)</span>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
# Match a single price number, with optional thousands separator and decimals.
_NUMBER_RE = re.compile(r"(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)")


def _parse_price(text: str) -> float | None:
    """
    Parse a single price (or midpoint of a range) out of an s-item__price block.
    Examples it handles:
      "C $19.99"                    -> 19.99
      "C $10.00 to C $25.00"        -> 17.5
      "$1,299.00"                   -> 1299.0
      "Free shipping"               -> None
    """
    # Strip any nested tags
    clean = _TAG_RE.sub(" ", text).replace("\xa0", " ").strip()
    if not clean:
        return None
    nums = _NUMBER_RE.findall(clean)
    if not nums:
        return None
    try:
        values = [float(n.replace(",", "")) for n in nums]
    except ValueError:
        return None
    if not values:
        return None
    # Range like "10.00 to 25.00" — use midpoint
    if len(values) >= 2:
        return round((min(values) + max(values)) / 2, 2)
    return round(values[0], 2)


def _extract_prices(html: str, max_results: int) -> list[float]:
    prices: list[float] = []
    for match in _PRICE_BLOCK_RE.finditer(html):
        p = _parse_price(match.group(1))
        if p is not None and p > 0:
            prices.append(p)
            if len(prices) >= max_results:
                break
    return prices


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * pct
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    return round(sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (k - lo), 2)


def _empty(query: str, error: str | None = None) -> dict:
    out = {"query": query, "count": 0, "currency": "CAD"}
    if error:
        out["error"] = error
    return out


async def fetch_sold_prices(query: str, max_results: int = 30) -> dict:
    """
    Search eBay CA sold/completed listings for `query` and return a price summary:
      {
        "query": str,
        "count": int,
        "min": float, "max": float,
        "median": float, "avg": float,
        "suggested": float,   # 40th percentile — slightly below median, sells faster
        "samples": [float, ...],
        "currency": "CAD"
      }
    On zero results or any network/parse failure, returns {count: 0, currency: "CAD"}.
    Never raises.
    """
    if not query or not query.strip():
        return _empty(query, "empty query")

    url = (
        "https://www.ebay.ca/sch/i.html"
        f"?_nkw={quote_plus(query.strip())}"
        "&LH_Sold=1&LH_Complete=1"
    )
    headers = {
        "User-Agent": UA,
        "Accept-Language": "en-CA,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.ebay.ca/",
    }

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
    except httpx.HTTPError as e:
        return _empty(query, f"network: {type(e).__name__}")

    if resp.status_code != 200:
        return _empty(query, f"http {resp.status_code}")

    try:
        prices = _extract_prices(resp.text, max_results)
    except Exception as e:  # defensive — never crash the caller
        return _empty(query, f"parse: {type(e).__name__}")

    if not prices:
        return _empty(query)

    prices_sorted = sorted(prices)
    return {
        "query": query,
        "count": len(prices_sorted),
        "min": round(min(prices_sorted), 2),
        "max": round(max(prices_sorted), 2),
        "median": round(statistics.median(prices_sorted), 2),
        "avg": round(statistics.mean(prices_sorted), 2),
        "suggested": _percentile(prices_sorted, 0.40),
        "samples": prices_sorted,
        "currency": "CAD",
    }


# Local smoke test:  python -m backend.services.ebay_scraper "vintage eames chair"
if __name__ == "__main__":
    import json, sys
    q = " ".join(sys.argv[1:]) or "vintage eames chair"
    print(json.dumps(asyncio.run(fetch_sold_prices(q)), indent=2))
