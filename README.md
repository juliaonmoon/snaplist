# SnapList

AI-powered cross-platform reselling assistant. Snap a photo — AI writes the title, description, and price — then post to Facebook Marketplace, eBay, Etsy, and Kijiji.

**Live app:** https://frontend-theta-six-98.vercel.app

**Stack:** FastAPI + PostgreSQL, React PWA (Vite), Chrome Extension MV3, Groq vision AI, Firebase Auth

---

## Local Development

### Backend

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in API keys (see below)
```

Start PostgreSQL, then run migrations and start the server:

```bash
# Quick PostgreSQL via Docker:
docker run -d --name snaplist-db \
  -e POSTGRES_USER=snaplist \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=snaplist \
  -p 5432:5432 postgres:16

alembic upgrade head
uvicorn backend.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
cp .env.example .env            # fill in Firebase keys
npm install
npm run dev
```

### Chrome Extension

Load unpacked from the `extension/` directory at `chrome://extensions`.

---

## Project Structure

```
snaplist/
├── backend/
│   ├── main.py               FastAPI app entry point
│   ├── config.py             Settings from .env
│   ├── database.py           SQLAlchemy async engine + session
│   ├── routes/               analyze, listings, inventory, platforms, notifications, profile
│   ├── services/             ai_analysis, price_research, ebay_api, etsy_api, daily_monitor,
│   │                         product_identifier, category_mapper
│   └── models/               user_profile, listing, inventory
├── frontend/                 React PWA (Vite)
│   └── src/
│       ├── App.jsx           Routing + auth guard
│       ├── AuthContext.jsx
│       ├── firebase.js
│       └── pages/            Login, Onboarding, Dashboard, NewListing, ListingDetail, Profile
├── extension/                Chrome Extension MV3 (autofills Facebook Marketplace)
├── cron/
│   └── daily_monitor.py      Standalone cron script
├── alembic/                  Database migrations
├── .github/workflows/        deploy-frontend.yml (GitHub Actions → GitHub Pages)
├── tests/
├── .env.example
└── requirements.txt
```

---

## API Keys

### Backend (`.env`)

| Variable | Cost | Where to get it |
|---|---|---|
| `GROQ_API_KEY` | Free, no card | [console.groq.com](https://console.groq.com) → API Keys |
| `DATABASE_URL` | — | PostgreSQL connection string |
| `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET` | Free developer account (approval pending) | [developer.ebay.com](https://developer.ebay.com) |
| `SENDGRID_API_KEY` | Free (100 emails/day) | [app.sendgrid.com](https://app.sendgrid.com) |
| `SERPAPI_KEY` | Free (250 searches/month) | [serpapi.com](https://serpapi.com) — used for Google Lens product ID |
| `ANTHROPIC_API_KEY` | Optional | Claude Vision fallback |

### Frontend (`frontend/.env`)

Firebase config variables (`VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, etc.) — from [Firebase Console](https://console.firebase.google.com), project `snaplist-a297c`.

---

## Deployment

### Vercel (current)

Frontend is deployed to Vercel automatically: https://frontend-theta-six-98.vercel.app

### GitHub Pages (pending — requires public repo)

A GitHub Actions workflow at `.github/workflows/deploy-frontend.yml` auto-deploys on every push to:
https://juliaonmoon.github.io/snaplist/

To enable:
1. Make the repo public — GitHub Settings → Danger Zone → Make public
2. Add `juliaonmoon.github.io` to Firebase Console → Authentication → Settings → Authorized domains

---

## Cron Job

```bash
# Run daily at 8 AM server time
0 8 * * * /path/to/venv/bin/python /path/to/cron/daily_monitor.py >> /var/log/snaplist-cron.log 2>&1
```
