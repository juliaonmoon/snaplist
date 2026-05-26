# SnapList Runbook

**Project:** SnapList — AI-powered cross-platform reselling assistant
**Repo:** juliaonmoon/snaplist (private)
**Owner:** Julia Cheng (juliaonmoon@gmail.com), Surrey, BC
**Dev branch:** `claude/hopeful-franklin-UYnIB`

> At the start of every session, read `HANDOFF.md`. At the end, update it and push.

---

## Services Overview

| Service | Local URL | Production |
|---------|-----------|------------|
| FastAPI backend | http://localhost:8000 | Not yet deployed |
| React frontend (dev) | http://localhost:5174 | https://frontend-theta-six-98.vercel.app (current) |
| React frontend (target) | — | https://juliaonmoon.github.io/snaplist/ (pending) |
| PostgreSQL 16 | localhost:5432 | Not yet deployed |
| Chrome Extension | — | Load unpacked from `extension/` |

---

## Starting Services (Local / Cloud Container)

```bash
# 1. PostgreSQL
pg_ctlcluster 16 main start

# 2. Backend
source venv/bin/activate
uvicorn backend.main:app --port 8000
# NOTE: Do NOT use --reload — it sometimes hangs and causes routes to 404.
# If routes return 404 after code changes, hard-kill uvicorn and restart.

# 3. Frontend dev server
cd frontend && node_modules/.bin/vite --port 5174
```

---

## Database

PostgreSQL 16, migrations via Alembic.

```bash
# Apply all pending migrations
alembic upgrade head

# Check current revision
alembic current

# Create a new migration after model changes
alembic revision --autogenerate -m "describe the change"
```

---

## Deployment

### Frontend — GitHub Pages (target, not yet live)

Auto-deploys via `.github/workflows/deploy-frontend.yml` on every push to `main` or `claude/hopeful-franklin-UYnIB` that touches `frontend/`.

**One-time setup required before this works:**
1. Make repo public: github.com/juliaonmoon/snaplist → Settings → Danger Zone → Change visibility → Make public
2. Add `juliaonmoon.github.io` to Firebase Console → Authentication → Settings → Authorized domains
3. After step 1, the next push to a watched branch triggers the workflow automatically

### Frontend — Vercel (current fallback)

- URL: https://frontend-theta-six-98.vercel.app
- No auto-deploy; requires manual redeploy in Vercel dashboard or connecting the GitHub repo in Vercel settings
- Note: Vercel (and Surge, Netlify) block requests from this cloud container's IP. Deployments must go through GitHub push, not direct upload.

---

## Firebase Auth

**Project ID:** snaplist-a297c
**Console:** https://console.firebase.google.com/project/snaplist-a297c

Firebase browser keys are public-facing by design — they are baked into `.github/workflows/deploy-frontend.yml` and live in `frontend/.env` (gitignored locally).

**Authorized domains** (manage at Firebase Console → Authentication → Settings):

| Domain | Status |
|--------|--------|
| localhost | Active |
| snaplist-a297c.firebaseapp.com | Active |
| frontend-theta-six-98.vercel.app | Needs confirmation |
| juliaonmoon.github.io | Add when Pages goes live |

---

## Testing

### Backend smoke tests

```bash
curl http://localhost:8000/health
curl http://localhost:8000/listings/?status_filter=draft
```

### Playwright (frontend)

Playwright is installed at `/opt/node22/bin/playwright` with Chromium. Always test against the local dev server — the Vercel URL is blocked from this container.

```bash
# Start dev server on port 5175 if not already running
cd frontend && node_modules/.bin/vite --port 5175 &

# Example test
node -e "
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await ctx.newPage();
  await page.goto('http://localhost:5175', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  console.log('URL:', page.url());
  console.log('Buttons:', await page.\$\$eval('button', els => els.map(e => e.textContent.trim())));
  await browser.close();
})();
"
```

---

## External Services

| Service | Purpose | Status | Console |
|---------|---------|--------|---------|
| Groq | AI vision (Llama 4 Scout) | Active | console.groq.com |
| SerpAPI | Google Lens product ID | Active (250 req/mo free) | serpapi.com |
| Firebase | Google + Facebook auth | Active | console.firebase.google.com |
| catbox.moe | Temporary public image hosting for SerpAPI | Active (anonymous) | catbox.moe |
| eBay API | Auto-post listings | Pending approval | developer.ebay.com |
| SendGrid | Daily digest email | Not set up | app.sendgrid.com |
| Anthropic (Claude) | Optional vision fallback | Not set up | console.anthropic.com |

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/routes/analyze.py` | `/analyze/photo` endpoint — calls Groq vision, product ID, assembles listing |
| `backend/services/ai_analysis.py` | Groq vision prompt (seller-voice, first-person) |
| `backend/services/product_identifier.py` | SerpAPI → Claude → Groq fallback chain with cache |
| `backend/services/category_mapper.py` | Maps listing to Facebook Marketplace category |
| `backend/data/fb_categories.json` | 26 flat FB Marketplace categories |
| `frontend/src/pages/Login.jsx` | Login/signup page (Get started / Log in toggle, Google + Facebook) |
| `frontend/src/pages/NewListing.jsx` | Photo upload + AI listing generation |
| `frontend/src/pages/Dashboard.jsx` | Listing grid |
| `frontend/src/AuthContext.jsx` | Auth state, onboarding flags per UID |
| `extension/content.js` | FB Marketplace autofill logic |
| `.github/workflows/deploy-frontend.yml` | Auto-deploy to GitHub Pages on push |
| `HANDOFF.md` | Session handoff notes — read at start, update at end |

---

## Known Issues and Quirks

1. **Groq null strings** — Groq returns the literal string `"null"` for missing fields. Sanitized by `_clean()` in `product_identifier.py` and `_denull()` in `analyze.py`.

2. **eBay scraper 403** — `ebay_scraper.py` gets HTTP 403 from Akamai bot detection. Use the official eBay API once approved.

3. **Facebook Marketplace CSP** — FB Marketplace blocks `fetch()` from page context to `localhost:8000`. The content script (`extension/content.js`) must do the fetch, not the page.

4. **uvicorn --reload hangs** — The `--reload` flag sometimes causes routes to return 404 after code changes. Hard-kill uvicorn and restart without `--reload`.

5. **Cloud container IP blocked** — Vercel, Surge, and Netlify block requests from this container's IP. Use GitHub push for all frontend deployments.

6. **SerpAPI quota** — Free tier is 250 requests/month. Results are cached in `product_identifier.py` to avoid burning quota on repeated lookups.
