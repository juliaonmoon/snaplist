# SnapList — Smart Cross-Platform Selling Assistant

> Snap it. Price it. List it everywhere.

## Quick Start

### 1. Install dependencies

```bash
cd snaplist
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials (see API Keys section below)
```

### 3. Start PostgreSQL

```bash
# Using Docker:
docker run -d \
  --name snaplist-db \
  -e POSTGRES_USER=snaplist \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=snaplist \
  -p 5432:5432 \
  postgres:16
```

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Start the API server

```bash
uvicorn backend.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

## Project Structure

```
snaplist/
├── backend/
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Settings from .env
│   ├── database.py           # SQLAlchemy async engine + session
│   ├── routes/
│   │   ├── analyze.py        # POST /analyze/photo (Gemini Flash vision)
│   │   ├── listings.py       # CRUD for listings
│   │   ├── inventory.py      # Platform listings + price history
│   │   ├── platforms.py      # Fee calc + posting logic
│   │   ├── notifications.py  # Notification log
│   │   └── profile.py        # User profile CRUD
│   ├── services/
│   │   ├── ai_analysis.py    # Gemini Flash vision integration (free tier)
│   │   ├── price_research.py # eBay sold listings market research
│   │   ├── ebay_api.py       # eBay Developer API
│   │   ├── etsy_api.py       # Etsy API v3
│   │   └── daily_monitor.py  # Cron job logic
│   └── models/
│       ├── user_profile.py
│       ├── listing.py
│       └── inventory.py      # PlatformListing, PriceHistory, NotificationLog
├── frontend/                 # React PWA (Step 4)
├── cron/
│   └── daily_monitor.py      # Standalone cron script
├── alembic/                  # Database migrations
├── .env.example
├── requirements.txt
└── README.md
```

---

## API Keys Needed

| Step | Key | Cost | Where to get it |
|------|-----|------|----------------|
| Step 2 | `GROQ_API_KEY` | **Free** (no card required) | [console.groq.com](https://console.groq.com) → API Keys |
| Step 3 | `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET` | Free developer account | [developer.ebay.com](https://developer.ebay.com) |
| Step 5 | `SENDGRID_API_KEY` | Free (100 emails/day) | [app.sendgrid.com](https://app.sendgrid.com) |

> **Note on AI vision:** The original spec called for Claude Vision (Anthropic API, paid).
> During prototyping, SnapList uses **Groq + Llama 4 Scout** for vision — completely free,
> no credit card required. You can swap to Claude or Gemini for production by updating
> `ai_analysis.py` and `config.py`.

---

## Cron Job (DigitalOcean)

```bash
# Run daily at 8 AM server time
0 8 * * * /path/to/venv/bin/python /path/to/cron/daily_monitor.py >> /var/log/snaplist-cron.log 2>&1
```

---

## Build Steps

- [x] **Step 1** — Backend API + PostgreSQL models
- [ ] **Step 2** — Gemini Flash photo analysis (free tier)
- [ ] **Step 3** — eBay API full integration
- [ ] **Step 4** — React PWA frontend (mobile-first, Android optimized)
- [ ] **Step 5** — Daily monitoring cron job + email digest
