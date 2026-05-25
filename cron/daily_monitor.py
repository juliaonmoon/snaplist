#!/usr/bin/env python3
"""
Standalone cron job — runs once every 24 hours on DigitalOcean.
Crontab entry: 0 8 * * * /path/to/venv/bin/python /path/to/cron/daily_monitor.py

Sends the daily digest email to the seller.
"""
import asyncio
import sys
from pathlib import Path

# Allow running from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from backend.config import settings
from backend.database import AsyncSessionLocal
from backend.services.daily_monitor import format_digest_email, run_daily_monitor


async def send_email(subject: str, body: str) -> None:
    """Send digest via SendGrid."""
    import httpx

    payload = {
        "personalizations": [{"to": [{"email": settings.notification_email}]}],
        "from": {"email": settings.from_email},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
            json=payload,
        )
        if resp.status_code not in (200, 202):
            print(f"[ERROR] SendGrid: {resp.status_code} {resp.text}")
        else:
            print("[OK] Daily digest email sent")


async def main():
    print("[SnapList] Daily monitor starting...")
    async with AsyncSessionLocal() as db:
        report = await run_daily_monitor(db)

    print(f"[SnapList] Report: {report['total_active']} active, "
          f"{len(report['sold_items'])} sold, "
          f"{len(report['price_alerts'])} alerts, "
          f"{len(report['markdown_suggestions'])} markdowns")

    body = format_digest_email(report)
    print(body)

    if settings.sendgrid_api_key and settings.notification_email:
        await send_email("SnapList Daily Update", body)
    else:
        print("[WARN] SendGrid not configured — email not sent. Set SENDGRID_API_KEY and NOTIFICATION_EMAIL in .env")


if __name__ == "__main__":
    asyncio.run(main())
