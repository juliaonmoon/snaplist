# SnapList — Current Status

_Last updated: 2026-05-25 (seller-voice rewrite)_

## 🎯 Product overview

**SnapList** is Julia Cheng's (Surrey, BC) AI-powered cross-platform reselling assistant. Snap a photo → AI fills in title, description, category, and suggested price → publish to Facebook Marketplace (pickup, fee-free), eBay, and Etsy.

- **Core user**: Julia — sells second-hand items, prefers FB Marketplace because pickup sales avoid eBay's 14% fee
- **Why it exists**: cross-posting the same item to multiple platforms is tedious; AI + a Chrome extension automate the boring parts
- **Primary platform**: Facebook Marketplace (Chrome extension autofills, since FB has no public posting API)
- **Secondary**: eBay (API when approved), Etsy (OAuth in v0.2)
- **Stack**: FastAPI + Postgres backend, React PWA frontend, Chrome extension MV3, Groq vision for AI
- **Roadmap**: v0.1 = FB autofill + eBay/Etsy stubs (now). v0.2 = real eBay API, Etsy OAuth, Kijiji.

## ✅ What works (verified end-to-end on real Facebook)

| Field | Mechanism | Status |
|---|---|---|
| Title | React-aware input setter (clears `_valueTracker`) | ✅ |
| Price | React-aware input setter | ✅ |
| Description | React-aware textarea setter | ✅ |
| Category | Flat dropdown → click matching `div[role="button"]` | ✅ |
| Condition | combobox + listbox `[role="option"]` | ✅ |
| Photos | DataTransfer to `input[type=file]` | ✅ (with placeholder image) |
| Location | `findByLabel(["location","city","where","address","pickup"])` | ✅ |

**Key insight**: FB Marketplace's Category is **flat**, not hierarchical. 26 top-level categories (Furniture, Tools, Garden, etc.) — no nested tree.

## ✅ AI product identification (added late session)

Hybrid identifier chain in `backend/services/product_identifier.py`:

1. **Cache lookup** — sha256 of photo bytes → `backend/data/id_cache.json`. Same photo = instant cached result, never re-hits paid APIs.
2. **SerpAPI Google Lens** — real reverse-image search. 250 free searches/mo. Photo first uploads anonymously to `catbox.moe` for a public URL.
3. **Claude Vision (Sonnet 4.6)** — fallback when Lens returns nothing. Requires `ANTHROPIC_API_KEY` (not set yet).
4. **Groq vision** — primary analysis baseline (always runs first).

**Verified working**: SerpAPI correctly identified an IKEA ÖRFJÄLL swivel chair from Julia's photo with high confidence. Browser displays Unicode (Ö/Ä) correctly; the "🔎 Identified" panel renders properly.

Response from `/analyze/photo` now includes: `brand`, `model`, `identified_product`, `identification_confidence`, `identification_source`, `official_specs`, `original_product_url`, `msrp_original`, `product_summary`, `seller_description`. The New Listing UI shows ID metadata in a blue panel and uses `seller_description` directly as the Description field.

## ✅ Seller-voice copy (added 05-25)

Listings are written **AS Julia, TO the buyer** — never AI-analyst voice. Fixed in three layers:

1. **Groq vision prompt** (`ai_analysis.py:ANALYSIS_PROMPT`) — explicitly tells the model it's writing as Julia in first-person, with an in-context example. Bans "appears to be / seem to be / the chair has".
2. **Backend description builder** (`routes/analyze.py`) — assembles the final description in seller voice: "Selling my <product>." → condition (seller voice) → notes → specs → MSRP → Google-lookup link.
3. **Title rewrite** — once identification confidence is high/medium, title becomes `"<identified_product> — <condition_word>"` (e.g. "ÖRFJÄLL swivel chair, white/Vissle light gray - IKEA — Good condition"), capped at 80 chars.

Frontend (`NewListing.jsx`) no longer assembles description client-side — it just reads `result.seller_description`.

## ✅ Onboarding & profile UX fixes

- **Logout button** added at the bottom of `Profile.jsx` — clears `localStorage.snaplist_onboarded` and redirects to onboarding.
- **Profile-step validation hint** — onboarding Continue button now greys out (50% opacity) and shows a red "Please fill in: <missing fields>" hint when required inputs are empty.
- **Honest eBay step** — was a fake 2-second simulated OAuth that flipped to "connected!". Replaced with a yellow "eBay developer approval pending — skip for now" notice. No green checkmark theater.

## 🚀 Local services (must be running for the extension to work)

| Service | URL | How to start |
|---|---|---|
| PostgreSQL 16 | `localhost:5432` | Windows service `postgresql-x64-16` — auto-starts |
| FastAPI backend | `http://localhost:8000` | `python -m uvicorn backend.main:app --port 8000` |
| React frontend | `http://localhost:5174` | `cd frontend && npm run dev` |

## 📦 Chrome extension

- **Location**: `C:\Users\jules\snaplist\extension\`
- **Load**: `chrome://extensions` → Developer mode ON → Load unpacked → select the folder
- **Reload after edits**: click 🔄 on its card
- **Test directory** was moved to `tests/extension/` (Chrome rejects `__test__` directory names)

## 🗂️ Important files

- `backend/data/fb_categories.json` — real flat FB Marketplace taxonomy (26 entries)
- `backend/data/id_cache.json` — sha256(photo) → identification cache (skips re-hitting paid APIs)
- `backend/services/category_mapper.py` — Groq AI maps our listing → FB category name
- `backend/services/ai_analysis.py` — Groq vision + `research_product()` (specs/URL lookup)
- `backend/services/product_identifier.py` — hybrid Google Lens → Claude → Groq orchestrator with hash cache + catbox.moe public-URL upload
- `backend/services/ebay_scraper.py` — eBay sold-listings price scraper (BLOCKED by Akamai bot detection — needs eBay API key)
- `backend/routes/analyze.py` — `/analyze/photo` endpoint; sanitizes Groq's literal-"null" strings, layers better identification on top
- `backend/seed_draft.py` — creates the demo Eames chair listing
- `extension/content.js` — fillListing logic + `pickCategoryByPath`
- `extension/popup.js` — fetches drafts + calls `/analyze/category` before sending
- `frontend/src/pages/Onboarding.jsx` — profile validation hint + honest eBay step
- `frontend/src/pages/Profile.jsx` — logout button at bottom
- `frontend/src/pages/NewListing.jsx` — blue "🔎 Identified" panel for product ID
- `tests/extension/test_navigator.py` — Playwright autonomous test against mock FB page (PASSES)

## ⏳ Pending

- **eBay developer approval** — until then, prices in `seed_draft.py` are mocked. When approved: swap `ebay_scraper.py` for the official Browse API.
- **SendGrid API key** — needed for daily digest emails. Sign up at app.sendgrid.com (free tier), add `SENDGRID_API_KEY` to `.env`.
- **Etsy OAuth** — currently shows "Coming soon" in onboarding/profile. v0.2.
- **`ANTHROPIC_API_KEY`** — optional Claude Vision fallback for product ID. Skipped this session; add only if SerpAPI quota gets tight or identification accuracy needs a second opinion. Pricing is prepaid; $5 lasts ~50 months at Julia's volume.
- **Per-marketplace pricing** — next big feature. Idea: use the Chrome extension (already runs in Julia's logged-in browser on FB/Kijiji/Craigslist) to scrape similar-item prices from each marketplace itself, send back to backend. Avoids ToS-violating server-side scraping. Whole-session work.
- **`research_product()` returns null URLs** — Groq doesn't know IKEA product URLs, so `original_product_url` and `msrp_original` stay null even when identification succeeds. Fix needs either a web-search tool (Tavily/Brave) or a model with stronger product knowledge.

## 🐛 Known quirks

- Backend's `--reload` flag sometimes hangs on file changes — if a route returns 404 after a code change, hard-kill all uvicorn-related Python processes and restart without `--reload`.
- eBay scraper returns HTTP 403 (Akamai bot detection) — code is correct, blocked at the network layer.
- Facebook Marketplace blocks `fetch()` from page-context to `localhost:8000` via CSP. The extension's content script can fetch (different security context) — page-context cannot.
- **Groq vision returns the literal STRING `"null"`** (four chars) instead of JSON `null` for missing fields. `product_identifier.py:_clean()` and `routes/analyze.py:_denull()` both sanitize this before it bleeds into identification logic or the cache. Without this, the cache would store "null" results and mask successful retries.
- **SerpAPI Google Lens requires a publicly reachable image URL** — localhost upload paths won't work. We POST anonymously to `catbox.moe/user/api.php` (no key needed) and pass the returned `https://files.catbox.moe/<id>.jpg` URL to SerpAPI. Originally tried `0x0.st` but it times out from Julia's network.
- **Windows terminal can't render `Ö`/`Ä`** — when debugging via `curl | python -c`, characters show as `Ã–`, `Ã„`, or `�`. The data in the FastAPI response is correct UTF-8 (verified by inspecting raw bytes `\xc3\x96`); only the Windows console rendering is broken. The browser displays them correctly. Don't waste time "fixing" what isn't broken.
- **Don't cache failed identifications** — `product_identifier.py:identify_product()` only caches when `identified_product` is a real value (not None, not the string "null"). Otherwise one bad search permanently masks a photo.

## 🌐 Live demo (frontend only)

Vercel: https://frontend-theta-six-98.vercel.app — runs against mock data when backend unreachable.

## 🧪 Quick smoke tests

```bash
# Backend health
curl http://localhost:8000/health

# Drafts
curl http://localhost:8000/listings/?status_filter=draft

# Category mapper
curl -X POST http://localhost:8000/analyze/category \
  -H "Content-Type: application/json" \
  -d '{"title":"Vintage Eames-style Lounge Chair","category":"Furniture","keywords":["eames","lounge chair"]}'
# expected: {"path":["Furniture"],"leaf":"Furniture","confidence":1.0}

# Product identification end-to-end (upload a real photo)
curl -X POST -F "photo=@uploads/<some>.jpg" -F "priority=balanced" -F "platform=facebook" \
  http://localhost:8000/analyze/photo
# expected on a known product: identified_product, brand, model populated;
#   identification_source: "google_lens"; identification_confidence: "high"

# Autonomous extension test (Playwright + mock FB page)
python tests/extension/test_navigator.py
```

## 📐 Conventions

- **UI tone / AI-written copy**: first-person seller voice, talking to a buyer. Never analyst voice. Never "appears to be", "seem to be", "the item has". When changing AI prompts, keep the seller-voice instruction + example.
- **Honest defaults**: never fake a "connected" state for services that aren't actually connected (see eBay step). Show pending/skipped honestly.
- **Don't cache failures**: only persist identification results when a real product is identified, not when the AI returns null/none-confidence.
- **Sanitize Groq output everywhere**: Groq returns the literal string `"null"` for missing fields. Run through `_clean()` / `_denull()` before any truthy check.
- **No emojis in code/docs** unless the user adds them or asks for them. UI emojis (📸 🔎) are fine because they're product copy.

## 🔑 Env vars (snaplist/.env)

- `GROQ_API_KEY` — set (free tier)
- `SERPAPI_KEY` — set (250 free searches; key value lives in `.env`)
- `ANTHROPIC_API_KEY` — empty (intentionally; optional fallback)
- `EBAY_*` — empty (pending eBay approval)
- `ETSY_*` — empty (v0.2)
- `SENDGRID_API_KEY` — empty (needed for digest emails)
