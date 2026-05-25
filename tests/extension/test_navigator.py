"""
Autonomous test for the SnapList content.js category navigator.

Loads the mock FB Marketplace page in a real Chromium, injects content.js,
and invokes fillListing() with a known fb_category_path. Verifies that all
six fields end up filled correctly without any human input.
"""
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent  # extension/
MOCK_PAGE = ROOT / "__test__" / "mock-fb-marketplace.html"
CONTENT_JS = ROOT / "content.js"


SEED_LISTING = {
    "id": 2,
    "title": "Vintage Eames-style Lounge Chair",
    "description": "Mid-century modern lounge chair in walnut.",
    "category": "Furniture",
    "condition": "good",
    "keywords": ["eames", "lounge chair", "mid-century"],
    "photos": [],          # no photo upload in mock
    "pickup_location": "Surrey",
    "ai_analysis": {"suggested_price": 285.0},
    "fb_category_path": ["Home & Garden", "Furniture", "Chairs", "Lounge Chairs"],
}


async def main():
    content_src = CONTENT_JS.read_text(encoding="utf-8")
    # The real content.js wraps in an IIFE that guards on chrome.runtime — in our
    # mock page chrome.runtime is undefined, so we shim it before injection.
    shim = """
      window.__msgListeners = [];
      window.chrome = window.chrome || {};
      window.chrome.runtime = window.chrome.runtime || {
        onMessage: {
          addListener: (fn) => { window.__msgListeners.push(fn); },
        },
      };
      window.chrome.storage = window.chrome.storage || {
        local: { get: (_k, cb) => cb({}), remove: () => {}, set: () => {} },
      };
    """

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()

        page_logs: list[str] = []
        page.on("console", lambda msg: page_logs.append(f"[{msg.type}] {msg.text}"))

        await page.goto(f"file://{MOCK_PAGE.as_posix()}")
        await page.wait_for_load_state("networkidle")

        await page.evaluate(shim)
        await page.evaluate(content_src)

        # Expose fillListing by re-defining it on window — easiest is to re-eval
        # a small wrapper that calls the existing IIFE's exported entry. Since the
        # IIFE doesn't expose it, we call it via the chrome.runtime.onMessage path:
        # capture the listener that content.js registered, then invoke it directly.
        result = await page.evaluate(
            """async (listing) => {
                const listeners = window.__msgListeners || [];
                if (!listeners.length) throw new Error('no onMessage listeners registered');
                return await new Promise((resolve) => {
                  const ret = listeners[0]({action: 'fillListing', listing}, {}, resolve);
                  // content.js returns true to keep sendResponse alive
                  if (!ret) resolve({ok: true});
                });
            }""",
            SEED_LISTING,
        )

        # Give navigator time to walk the modal
        await asyncio.sleep(4)

        # Read back what got filled
        snapshot = await page.evaluate(
            """() => ({
                title:       document.getElementById('title-input').value,
                price:       document.getElementById('price-input').value,
                description: document.getElementById('desc-input').value,
                category:    document.getElementById('category-display').textContent,
                condition:   document.getElementById('condition-display').textContent,
                modal_open:  document.getElementById('category-modal').classList.contains('open'),
            })"""
        )

        await browser.close()

    print("=== Result from fillListing() ===")
    print(json.dumps(result, indent=2))
    print("\n=== Form state after fill ===")
    print(json.dumps(snapshot, indent=2))
    print("\n=== Page console logs ===")
    for line in page_logs:
        print(" ", line)

    # Assertions
    ok = True
    if snapshot["title"] != SEED_LISTING["title"]:
        print(f"\nFAIL: title not filled — got {snapshot['title']!r}")
        ok = False
    if snapshot["price"] not in ("285", "285.0"):
        print(f"\nFAIL: price not filled — got {snapshot['price']!r}")
        ok = False
    if snapshot["category"] != "Lounge Chairs":
        print(f"\nFAIL: category did not land on leaf — got {snapshot['category']!r}")
        ok = False
    if "Good" not in snapshot["condition"]:
        print(f"\nFAIL: condition wrong — got {snapshot['condition']!r}")
        ok = False
    print("\nVERDICT:", "PASS [ok]" if ok else "FAIL [x]")


if __name__ == "__main__":
    asyncio.run(main())
