"""
Seed a single test draft listing so the Chrome extension has something to
fill into Facebook Marketplace immediately. Idempotent — safe to re-run.

Usage:  python backend/seed_draft.py
"""
import asyncio
from pathlib import Path

from sqlalchemy import select

from backend.database import AsyncSessionLocal
from backend.models.listing import (
    Condition,
    Listing,
    ListingStatus,
    Priority,
    ShippingPreference,
)
from backend.models.user_profile import (
    DefaultPriority,
    UserProfile,
)
from backend.models.user_profile import ShippingPreference as UserShippingPref

SEED_TITLE = "Vintage Eames-style Lounge Chair"
SEED_PHOTO = "uploads/seed-chair.jpg"


def _generate_placeholder_image(path: Path) -> bool:
    """Generate a 600x600 placeholder JPG with 'CHAIR' centered. Returns True on success."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (600, 600), (139, 90, 43))  # walnut brown
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 96)
    except Exception:
        font = ImageFont.load_default()
    text = "CHAIR"
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        tw, th = 200, 60
    draw.text(((600 - tw) / 2, (600 - th) / 2 - 20), text, fill=(245, 235, 215), font=font)
    img.save(path, "JPEG", quality=85)
    return True


async def seed():
    async with AsyncSessionLocal() as db:
        # 1. Ensure a user with id=1 exists
        result = await db.execute(select(UserProfile).where(UserProfile.id == 1))
        user = result.scalar_one_or_none()
        if user is None:
            user = UserProfile(
                id=1,
                name="Julia Cheng",
                email="juliaonmoon@gmail.com",
                location="Surrey, BC, Canada",
                pickup_location="Tim Hortons on 152nd St, Surrey",
                default_priority=DefaultPriority.balanced,
                default_shipping_preference=UserShippingPref.both,
                default_markdown_percent=10.0,
                default_markdown_days=14,
                default_floor_price=0.0,
            )
            db.add(user)
            await db.flush()
            print(f"[ok] Created UserProfile id=1 ({user.email})")
        else:
            print(f"[--] UserProfile id=1 already exists ({user.email})")

        # 2. Generate placeholder photo if Pillow is around
        photo_path = Path(SEED_PHOTO)
        if not photo_path.exists():
            if _generate_placeholder_image(photo_path):
                print(f"[ok] Generated placeholder photo at {photo_path}")
            else:
                print(f"[--] Skipped placeholder photo (Pillow unavailable)")
        else:
            print(f"[--] Photo already exists at {photo_path}")

        # 3. Skip insert if a draft with this title already exists
        result = await db.execute(
            select(Listing).where(
                Listing.title == SEED_TITLE,
                Listing.status == ListingStatus.draft,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"[--] Draft already exists: id={existing.id} '{existing.title}' — nothing to do")
            return

        listing = Listing(
            user_id=1,
            title=SEED_TITLE,
            description=(
                "Mid-century modern lounge chair in walnut with original cream leather. "
                "Great vintage condition — light patina on the wood, no tears in the upholstery. "
                "Comfortable for reading or movies. Pickup in Surrey."
            ),
            category="Furniture",
            condition=Condition.good,
            condition_description="Light patina on wood; upholstery clean with no tears.",
            keywords=["eames", "lounge chair", "mid-century", "walnut", "vintage"],
            dimensions="32\" W x 33\" D x 33\" H",
            status=ListingStatus.draft,
            priority=Priority.balanced,
            shipping_preference=ShippingPreference.pickup_only,
            quantity=1,
            quantity_available=1,
            quantity_sold=0,
            photos=[f"/{SEED_PHOTO}"],
            ai_analysis={
                "suggested_price": 285.0,
                "market": {
                    "count": 12,
                    "min": 180.0,
                    "max": 520.0,
                    "median": 295.0,
                    "avg": 310.0,
                    "suggested": 285.0,
                    "currency": "CAD",
                    "note": "mocked — real eBay scraper blocked by Akamai; awaiting eBay API key",
                },
            },
            markdown_percent=10.0,
            markdown_days=14,
            floor_price=200.0,
        )
        db.add(listing)
        await db.commit()
        await db.refresh(listing)
        print(f"[ok] Created draft listing id={listing.id}: '{listing.title}'")
        print(f"  Suggested price: C$ {listing.ai_analysis['suggested_price']}")
        print(f"  Photo: {listing.photos[0]}")


if __name__ == "__main__":
    asyncio.run(seed())
