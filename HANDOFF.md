# SnapList — Session Handoff

_Written: 2026-05-26_

## ⚡ In-flight work

**GitHub Pages deployment is triggered but not yet confirmed live.**

The React PWA was migrated from Vercel to GitHub Pages this session. All code is merged to `main`. The workflow builds cleanly locally (`npm ci && npm run build` → 275ms, no errors). The URL is `https://juliaonmoon.github.io/snaplist/` — currently returning HTTP 403.

**Most likely cause of 403**: GitHub Pages was just activated. The deploy workflow needs to complete one successful run for the CDN to start serving. Check `github.com/juliaonmoon/snaplist/actions` — if the "Deploy to GitHub Pages" workflow shows red, look at the deploy job logs.

**One thing to verify in GitHub UI**: go to `Settings → Pages` and confirm Source still reads "GitHub Actions". If it reverted, re-select it. That's the only manual step needed.

## 🆕 Done this session

### 1. GitHub Pages pipeline
- Added `.github/workflows/deploy.yml` — builds React frontend, deploys to `github-pages` environment on every push to `main`
- Added `base: '/snaplist/'` to `frontend/vite.config.js` so Vite asset paths work under the subdirectory
- Target URL: `https://juliaonmoon.github.io/snaplist/`
- Vercel URL still works (`https://frontend-theta-six-98.vercel.app`) — safe to delete once Pages is confirmed live

### 2. Login flow for returning users
- Welcome screen (`Onboarding.jsx` step 0) now has two buttons: **"Get started →"** (new user) and **"Log in"** (returning user)
- Login view: asks for email → checks `localStorage.snaplist_user_email` first (instant, offline-capable) → falls back to `api.profile.get(1)` if no local match → on success, sets session and goes to Dashboard
- `finish()` in Onboarding now persists `localStorage.setItem('snaplist_user_email', form.email)` so future logins don't need a network round-trip
- "Get started instead" link lets them switch back from login view

## ❓ Still open

- **GitHub Pages live confirmation** — need one green Actions run. Should auto-resolve on the next push to `main`.
- **Firebase authorized domains** — add `juliaonmoon.github.io` to Firebase console → Authentication → Settings → Authorized domains (needed if/when Firebase Auth is wired up)
- **eBay developer approval** — pending. Swap `ebay_scraper.py` for official Browse API when approved.
- **SendGrid API key** — needed for daily digest emails. Add `SENDGRID_API_KEY` to `.env`.
- **`research_product()` returns null URLs** — Groq doesn't know live product URLs. Fix needs Tavily/Brave web-search tool.
- **Per-marketplace pricing** — use Chrome extension to scrape similar-item prices from each marketplace (whole-session work, deferred).
- **`ANTHROPIC_API_KEY`** — intentionally empty. Claude Vision tier-2 identification activates automatically once added.

## 🗺️ Repo layout

```
snaplist/
├── .github/workflows/deploy.yml   ← GitHub Pages CI/CD
├── frontend/                      ← React PWA (Vite + React 19)
│   ├── src/
│   │   ├── App.jsx                ← routing + auth gate (localStorage)
│   │   ├── api.js                 ← all backend calls
│   │   ├── index.css
│   │   └── pages/
│   │       ├── Onboarding.jsx     ← welcome + login flow
│   │       ├── Dashboard.jsx
│   │       ├── NewListing.jsx     ← photo upload → AI analysis → post
│   │       ├── ListingDetail.jsx
│   │       └── Profile.jsx        ← logout button at bottom
│   └── vite.config.js             ← base: '/snaplist/' for Pages
├── backend/                       ← FastAPI + Postgres
│   ├── routes/
│   │   ├── analyze.py             ← /analyze/photo — main AI endpoint
│   │   ├── listings.py
│   │   ├── platforms.py
│   │   ├── profile.py
│   │   └── notifications.py
│   ├── services/
│   │   ├── ai_analysis.py         ← Groq vision + seller-voice prompts
│   │   ├── product_identifier.py  ← Google Lens → Claude Vision → Groq chain
│   │   ├── ebay_api.py
│   │   └── daily_monitor.py
│   └── data/
│       ├── fb_categories.json     ← 26 flat FB Marketplace categories
│       └── id_cache.json          ← sha256(photo) → identification cache
└── extension/                     ← Chrome MV3 extension
    ├── content.js                 ← fillListing + pickCategoryByPath
    └── popup.js
```

## 🔑 Env vars (backend/.env)

| Key | Status |
|---|---|
| `GROQ_API_KEY` | set |
| `SERPAPI_KEY` | set (250 free searches/mo) |
| `ANTHROPIC_API_KEY` | empty — optional Claude Vision fallback |
| `EBAY_*` | empty — pending eBay approval |
| `ETSY_*` | empty — v0.2 |
| `SENDGRID_API_KEY` | empty — needed for digest emails |

## 🚀 Local dev

```bash
# Backend
python -m uvicorn backend.main:app --port 8000

# Frontend
cd frontend && npm run dev   # http://localhost:5174
```

## 📐 Conventions (never break these)

- **Seller voice**: AI copy is written AS Julia TO the buyer. Never "appears to be", "the item has". First-person, natural.
- **Groq returns literal `"null"`**: sanitize with `_clean()` / `_denull()` before any truthy check or cache write.
- **Don't cache failed IDs**: `product_identifier.py` only caches when `identified_product` is a real value.
- **Honest UI**: never fake a "connected" state for services not actually connected.

## 🐛 Known quirks

- eBay scraper (`ebay_scraper.py`) blocked by Akamai — code is correct, network-layer block. Waiting on official API.
- FB Marketplace blocks `fetch()` from page-context to `localhost:8000` (CSP). Extension content script can fetch; page-context cannot.
- `catbox.moe` used for anonymous image hosting so SerpAPI (Google Lens) can reach a public URL. No API key needed.
- Backend `--reload` sometimes hangs — hard-kill uvicorn and restart without `--reload` if a route 404s after code changes.

## 🧪 Quick smoke tests

```bash
curl http://localhost:8000/health

# End-to-end photo analysis
curl -X POST -F "photo=@<some>.jpg" -F "priority=balanced" -F "platform=facebook" \
  http://localhost:8000/analyze/photo
```

## 📜 Git log

```
a0ce8b4 ci: retrigger Pages deployment
47e21c3 feat: add login path for returning users on welcome screen
fe463c6 trigger: kick off first GitHub Pages deployment
c52c348 Add GitHub Pages deploy workflow and Vite base path (#1)
53792bf Initial commit: SnapList v0.1
```
