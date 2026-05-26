# SnapList — Session Handoff

_Updated: 2026-05-26 (session 2)_

## ⚡ In-flight work

**Firebase env vars ARE set in Vercel. Login code is confirmed correct locally. Need to diagnose Vercel behavior.**

### What was proven with Playwright (autonomous browser testing)
- **Without Firebase env vars** → app correctly shows "Firebase not configured" at `/login` ✅
- **With Firebase env vars** → app correctly shows Google + Facebook buttons at `/login` ✅
- So the login code is NOT the problem.

### Current mystery — Vercel shows Onboarding screen instead of Login
Julia opens `https://frontend-theta-six-98.vercel.app` (even in incognito) and sees
**"Welcome to SnapList" with "Get started →"** — the onboarding screen (`/onboarding`),
not the login screen.

**Most likely explanation (to confirm next session):**
The app is routing to `/onboarding` which means it thinks Julia IS logged in.
This could mean she has a persisted Google auth session in the incognito window's
IndexedDB from a prior attempt (all incognito tabs in the same Chrome session share storage).
If she previously clicked "Continue with Google" and Firebase auth partially worked,
the session could be cached — and she's now logged in but not onboarded.

**This could actually be GOOD news** — it may mean Google login IS working.
She just needs to complete onboarding.

### First things to try next session
1. On the Vercel app: **check the URL bar** — does it say `/onboarding`?
2. If yes — just tap "Get started" and complete the onboarding flow! May already be logged in.
3. If onboarding completes → great, Google login worked earlier without her realizing it.
4. If onboarding fails (can't complete) → check DevTools → Application → IndexedDB → Firebase

### If Google login is NOT working yet
- Firebase authorized domain still needed: Firebase Console → Authentication →
  Settings → Authorized domains → Add `frontend-theta-six-98.vercel.app`
- To force a fresh login: DevTools → Application → clear site data, then reload

### Other pending work
- Connect Vercel to GitHub for auto-deploys
- eBay developer approval (external)
- SendGrid API key (for digest emails)

## 🚀 Deployment Status

### What's set up
`.github/workflows/deploy-frontend.yml` is pushed and ready. On every push to
`claude/hopeful-franklin-UYnIB` or `main`, it builds the Vite frontend and deploys to
**https://juliaonmoon.github.io/snaplist/** automatically — zero manual steps after setup.

### Two one-time actions needed from Julia
1. **Make the repo public**: `github.com/juliaonmoon/snaplist` → Settings → Danger Zone →
   Change visibility → Make public.
   (Repo is currently private; GitHub Pages is free only for public repos.)

2. **Add GitHub Pages domain to Firebase**: Firebase Console → Authentication →
   Settings → Authorized domains → Add `juliaonmoon.github.io`
   (Without this, Google/Facebook login will be blocked on the Pages URL.)

### Why I can't deploy from this container
Every external hosting service (Vercel, Surge, Netlify) blocks requests from this
cloud container's IP ("Host not in allowlist"). Only GitHub push via the internal
proxy works. GitHub Pages via Actions is the only fully autonomous path.

### Vercel (existing deployment)
Still live at `https://frontend-theta-six-98.vercel.app`. To make Vercel auto-deploy:
go to the Vercel dashboard → connect the GitHub repo. But GitHub Pages is simpler.

## 🤖 Autonomous Testing Setup (NEW)
Playwright + Chromium is installed globally at `/opt/node22/bin/playwright`.
Use it like this for any UI testing without needing Julia to interact:

```js
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ ignoreHTTPSErrors: true });
const page = await context.newPage();
await page.goto('http://localhost:5175', { waitUntil: 'networkidle' });
// check url, click buttons, fill forms, etc.
```

**Note:** Vercel blocks requests from this cloud container (403 "Host not in allowlist").
Always test against the local dev server (`http://localhost:5175`).
To start the dev server: `cd /home/user/snaplist/frontend && node_modules/.bin/vite --port 5175 &`
Frontend `node_modules` must be installed first: `cd frontend && npm install`
Firebase `.env` is at `frontend/.env` (keys already written — see below).

## ❓ Open decisions / pending

- **Vercel env vars** — not set yet. Julia will do this when she has time. Keys are in this handoff doc (see below).
- **Facebook Login** — not set up yet. Google only for now. Add later via Facebook Developer App.
- **Firebase Authorized Domains** — `localhost` is already there. When testing on Vercel, add `frontend-theta-six-98.vercel.app` in Firebase Console → Authentication → Settings → Authorized domains.
- **Backend auth** — still single-user, USER_ID=1 hardcoded in Profile.jsx. Firebase UID not yet wired to the backend profile. Fine for now (Julia is the only user). Future work.
- **Seller-voice fix** — verified correct via in-container test. Not yet tested with a real photo (needs GROQ_API_KEY in this environment, or test locally).
- **ANTHROPIC_API_KEY** — still skipped (Claude Vision fallback, add later if SerpAPI quota tightens).
- **eBay / Etsy / SendGrid** — all still pending/deferred.

## 🔑 Firebase config (snaplist-a297c)

Add these to Vercel → project → Settings → Environment Variables → redeploy.
Also add to local `snaplist/frontend/.env` after pulling the branch.

```
VITE_FIREBASE_API_KEY=AIzaSyDzcYIkB60OgBkcor4YhVqqdUCeDNkQboE
VITE_FIREBASE_AUTH_DOMAIN=snaplist-a297c.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=snaplist-a297c
VITE_FIREBASE_STORAGE_BUCKET=snaplist-a297c.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=634566313776
VITE_FIREBASE_APP_ID=1:634566313776:web:ab0cbcd1422af819c4eaf5
```

## 🆕 What was done this session

1. **Seller-voice fix verified** — description builder in `routes/analyze.py` confirmed correct. Output starts "Selling my X.", no banned phrases, reads as Julia talking to a buyer.
2. **Initial Alembic migration generated** — `alembic/versions/27fcfaadbc1c_initial_schema.py` created and applied. DB schema now in version control.
3. **Google + Facebook social login added**:
   - `frontend/src/firebase.js` — Firebase init (only if VITE_FIREBASE_API_KEY is set)
   - `frontend/src/AuthContext.jsx` — auth state, isOnboarded/setOnboarded scoped per UID
   - `frontend/src/pages/Login.jsx` — Google + Facebook buttons, honest "not configured" fallback
   - `frontend/src/App.jsx` — routes: unauthenticated → /login, new user → /onboarding, returning → /
   - `frontend/src/pages/Onboarding.jsx` — pre-fills name/email from social provider
   - `frontend/src/pages/Profile.jsx` — shows provider avatar photo, logout calls Firebase signOut()
   - `frontend/.env.example` — documents required VITE_FIREBASE_* keys

## 🚦 Services state (cloud container)

- Backend `localhost:8000` — ✅ up (uvicorn, no --reload)
- Frontend `localhost:5174` — ✅ up (Vite)
- Postgres — ✅ up (pg_ctlcluster 16 main)
- Note: cloud container ports are not browser-accessible. Use Vercel for live testing.

## 📁 Project path (cloud container)

- **cwd**: `/home/user/snaplist`
- **branch**: `claude/funny-meitner-ORmWh`
