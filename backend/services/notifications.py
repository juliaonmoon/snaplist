"""
Notification service — email via SendGrid, optional push via Pushover.
Free tier: SendGrid 100 emails/day, Pushover one-time $5 lifetime.
"""
import httpx

from backend.config import settings


async def send_email(subject: str, body: str, to: str | None = None) -> bool:
    """Send an email via SendGrid. Returns True on success."""
    recipient = to or settings.notification_email
    if not settings.sendgrid_api_key or not recipient:
        print(f"[notify] SendGrid not configured — would have sent: {subject}")
        return False

    payload = {
        "personalizations": [{"to": [{"email": recipient}]}],
        "from": {"email": settings.from_email, "name": "SnapList"},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {settings.sendgrid_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
    if resp.status_code in (200, 202):
        print(f"[notify] Email sent to {recipient}: {subject}")
        return True
    print(f"[notify] SendGrid error {resp.status_code}: {resp.text}")
    return False


async def send_push(message: str, title: str = "SnapList") -> bool:
    """Send a push notification via Pushover (optional)."""
    if not settings.pushover_app_token or not settings.pushover_user_key:
        return False

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token":   settings.pushover_app_token,
                "user":    settings.pushover_user_key,
                "title":   title,
                "message": message,
            },
            timeout=10,
        )
    return resp.status_code == 200


async def notify_sold(item_title: str, platform: str, price: float, currency: str = "CAD") -> None:
    """Alert the seller that an item sold."""
    subject = f"✅ Sold: {item_title}"
    body = (
        f"Great news! Your listing sold on {platform.capitalize()}.\n\n"
        f"Item: {item_title}\n"
        f"Sale price: {currency} ${price:.2f}\n\n"
        f"Remember to mark it as sold on any other platforms where it's still listed.\n\n"
        f"— SnapList"
    )
    await send_email(subject, body)
    await send_push(f"{item_title} sold on {platform} for {currency} ${price:.2f}!", title="Item Sold!")


async def notify_price_alert(item_title: str, current_price: float, suggested_price: float, currency: str = "CAD") -> None:
    """Alert seller their price is above market."""
    subject = f"📉 Price Alert: {item_title}"
    body = (
        f"Your listing may be priced above market.\n\n"
        f"Item: {item_title}\n"
        f"Your price: {currency} ${current_price:.2f}\n"
        f"Suggested price: {currency} ${suggested_price:.2f}\n\n"
        f"Log in to SnapList to approve or dismiss this recommendation.\n\n"
        f"— SnapList"
    )
    await send_email(subject, body)


async def send_daily_digest(digest_text: str) -> None:
    """Send the full daily digest email."""
    await send_email("SnapList Daily Update", digest_text)
