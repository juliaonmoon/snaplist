# SnapList — Session Handoff

_Updated: 2026-05-26 (session 3)_

## ⚡ What needs to happen next (Julia does these — 60 seconds total)

1. **Make repo public**: `github.com/juliaonmoon/snaplist` → Settings → Danger Zone →
   Change visibility → Make public.
   → This triggers GitHub Actions automatically. App deploys to https://juliaonmoon.github.io/snaplist/

2. **Add Firebase authorized domain**: Firebase Console → Authentication → Settings →
   Authorized domains → Add `juliaonmoon.github.io`
   → Without this, Google/Facebook login will fail on the new URL.

Once those two are done: **Vercel can be deleted.** GitHub Pages is the permanent home.

---

## 🚀 Deployment

| URL | Status |
|-----|--------|
| https://frontend-theta-six-98.vercel.app | Live (Vercel, manual redeploy, temporary) |
| https://juliaonmoon.github.io/snaplist/ | Ready — activates when repo is made public |

Auto-deploy workflow: `.github/workflows/deploy-frontend.yml`
Triggers on every push to `main` or `claude/hopeful-franklin-UYnIB` that touches `frontend/`.

---

## ✅ What was done this session

1. **Login page redesigned** — now shows feature list + two modes:
   - "Get started" (new users) and "Log in" (returning users), toggled by a link
   - Both use the same Google + Facebook OAuth — Firebase handles new vs. returning
   - Verified working with Playwright against local dev server

2. **GitHub Actions deployment set up** — `.github/workflows/deploy-frontend.yml`
   builds Vite frontend and deploys to GitHub Pages on every push. Firebase keys
   baked into workflow (they're public browser keys, not secrets).

3. **vite.config.js** — supports `GITHUB_PAGES=true` env var to set `/snaplist/` base path
4. **App.jsx** — BrowserRouter uses `import.meta.env.BASE_URL` for basename (works for both Vercel and GitHub Pages)
5. **Documentation updated**:
   - `README.md` — rewritten with current stack, structure, deployment steps
   - `STATUS.md` — added Firebase auth section, deployment section, live URLs table
   - `RUNBOOK.md` — new operational reference (services, deployment, testing, quirks)

---

## 🔍 Outstanding mystery (low priority)

When Julia visited the Vercel URL, she saw the Onboarding screen instead of Login —
even in incognito. This suggests Firebase auth may have already been working and she
had a cached Google session. Once GitHub Pages is live and she logs in fresh there,
this probably resolves itself. If not: DevTools → Application → Clear site data → reload.

---

## 🤖 Autonomous testing

Playwright + Chromium at `/opt/node22/lib/node_modules/playwright`.
Always test against local dev server (Vercel/external hosts block this container's IP).

```bash
# Start dev server
cd /home/user/snaplist/frontend && node_modules/.bin/vite --port 5175 &

# Run a test
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

`frontend/node_modules` must be installed first: `cd frontend && npm install`
Firebase `.env` is already written at `frontend/.env`.

---

## ⏳ Pending (not urgent)

- **eBay developer approval** — external, waiting
- **SendGrid API key** — for digest emails, sign up at app.sendgrid.com
- **Facebook Login** — Firebase has it wired up; needs a Facebook Developer App created
- **Backend auth** — USER_ID=1 hardcoded in Profile.jsx; Firebase UID not yet wired to backend profile (fine while Julia is the only user)
- **Anthropic API key** — optional Claude Vision fallback; skip until SerpAPI quota gets tight

---

## 🔑 Firebase config (snaplist-a297c)

```
VITE_FIREBASE_API_KEY=AIzaSyDzcYIkB60OgBkcor4YhVqqdUCeDNkQboE
VITE_FIREBASE_AUTH_DOMAIN=snaplist-a297c.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=snaplist-a297c
VITE_FIREBASE_STORAGE_BUCKET=snaplist-a297c.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=634566313776
VITE_FIREBASE_APP_ID=1:634566313776:web:ab0cbcd1422af819c4eaf5
```

---

## 📁 Session info

- **Repo**: juliaonmoon/snaplist
- **Branch**: claude/hopeful-franklin-UYnIB
- **Local path**: /home/user/snaplist
