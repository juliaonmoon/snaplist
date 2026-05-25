# SnapList — Session Handoff

_Written: 2026-05-25_

## ⚡ In-flight work

**Firebase auth is wired up but Vercel env vars still need to be added.**

Login page, AuthContext, and routing are all committed and pushed to `claude/funny-meitner-ORmWh`. The Firebase project (`snaplist-a297c`) is created and Google sign-in is enabled. The `frontend/.env` in this cloud container has the keys. Vercel does not yet have the env vars, so the live site still shows "Firebase not configured."

Next concrete step: Julia adds the 6 `VITE_FIREBASE_*` env vars to Vercel (Settings → Environment Variables), then redeploys. After that, test Google login on the live Vercel URL and confirm the auth flow works end-to-end.

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
