# SnapList — Session Handoff

_Written: 2026-05-25_

## ⚡ In-flight work

**Waiting on Julia to test the seller-voice rewrite.**

Last action: restarted backend (`bj9201so8`) after wiring up the seller-voice description builder. Vite frontend still running. Browser-side test not yet done.

Next concrete step: Julia hard-refreshes the New Listing page, re-uploads the ÖRFJÄLL chair photo (or a fresh photo), and verifies the Description field reads naturally as if she's talking to a buyer — NOT "the chair appears to be" / "Condition:" with colons. If the condition line still sounds AI-ish, the Groq prompt needs another pass.

## ❓ Open decisions

- **None active.** Julia's earlier deferrals still stand:
  - `ANTHROPIC_API_KEY` skipped (Claude Vision fallback — add later if SerpAPI quota tightens)
  - eBay onboarding fix deferred ("leave it, fix later")
  - Per-marketplace pricing deferred (whole-session work)

## 🆕 New gotchas this session

_(All folded into STATUS.md — Seller-voice section + Conventions section. Nothing pending migration.)_

## 📁 Project path

- **cwd**: `C:\Users\jules\snaplist`
- **Claude project dir**: `C:\Users\jules\.claude\projects\C--Users-jules\`

Encoded from `C:\Users\jules` (where the parent shell launched), not from `snaplist/`. Resume should `cd snaplist` first.

## 🚦 Services state at handoff

- Backend `localhost:8000` — ✅ up (bg task `bj9201so8`, no `--reload`)
- Frontend `localhost:5174` — ✅ up (bg task `bvc5xdeko`, Vite HMR active)
- Postgres — ✅ assumed up
- `backend/data/id_cache.json` — present, holds last successful Lens identification (sha256 → result)

## 📜 Transcript path

`C:\Users\jules\.claude\projects\C--Users-jules\d2a4d04d-1078-43c0-89cf-d41d27893f0f.jsonl`

Grep only on demand — do not read eagerly.
