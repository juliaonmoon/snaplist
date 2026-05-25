from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Listing, ListingStatus

router = APIRouter(prefix="/listings", tags=["listings"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class ListingCreate(BaseModel):
    user_id: int
    title: str
    description: str | None = None
    category: str | None = None
    condition: str | None = None
    condition_description: str | None = None
    keywords: list[str] | None = None
    dimensions: str | None = None
    priority: str = "balanced"
    shipping_preference: str = "both"
    quantity: int = 1
    markdown_percent: float | None = None
    markdown_days: int | None = None
    floor_price: float | None = None


class ListingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    condition: str | None = None
    condition_description: str | None = None
    keywords: list[str] | None = None
    dimensions: str | None = None
    priority: str | None = None
    shipping_preference: str | None = None
    quantity: int | None = None
    markdown_percent: float | None = None
    markdown_days: int | None = None
    floor_price: float | None = None
    status: str | None = None


class ListingOut(BaseModel):
    id: int
    user_id: int
    title: str
    description: str | None
    category: str | None
    condition: str | None
    condition_description: str | None
    keywords: list[str] | None
    dimensions: str | None
    status: str
    priority: str
    shipping_preference: str
    quantity: int
    quantity_available: int
    quantity_sold: int
    photos: list[str] | None
    ai_analysis: dict | None
    ebay_listing_id: str | None
    etsy_listing_id: str | None
    markdown_percent: float | None
    markdown_days: int | None
    floor_price: float | None
    created_at: datetime
    updated_at: datetime
    listed_at: datetime | None
    sold_at: datetime | None

    model_config = {"from_attributes": True}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[ListingOut])
async def get_listings(
    user_id: int | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Listing)
    if user_id:
        q = q.where(Listing.user_id == user_id)
    if status_filter:
        q = q.where(Listing.status == status_filter)
    result = await db.execute(q.order_by(Listing.created_at.desc()))
    return result.scalars().all()


@router.get("/{listing_id}", response_model=ListingOut)
async def get_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.post("/", response_model=ListingOut, status_code=status.HTTP_201_CREATED)
async def create_listing(data: ListingCreate, db: AsyncSession = Depends(get_db)):
    listing = Listing(
        **data.model_dump(),
        quantity_available=data.quantity,
    )
    db.add(listing)
    await db.flush()
    await db.refresh(listing)
    return listing


@router.patch("/{listing_id}", response_model=ListingOut)
async def update_listing(
    listing_id: int, data: ListingUpdate, db: AsyncSession = Depends(get_db)
):
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(listing, field, value)
    await db.flush()
    await db.refresh(listing)
    return listing


@router.post("/{listing_id}/publish", response_model=ListingOut)
async def publish_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    """Transition a listing from draft → active and stamp listed_at."""
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != ListingStatus.draft:
        raise HTTPException(status_code=400, detail=f"Listing is already {listing.status}")
    listing.status = ListingStatus.active
    listing.listed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(listing)
    return listing


@router.post("/{listing_id}/sold", response_model=ListingOut)
async def mark_sold(listing_id: int, platform: str | None = None, db: AsyncSession = Depends(get_db)):
    """Mark a listing as sold, decrement inventory, stamp sold_at."""
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.quantity_sold += 1
    listing.quantity_available = max(0, listing.quantity_available - 1)
    if listing.quantity_available == 0:
        listing.status = ListingStatus.sold
        listing.sold_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(listing)
    return listing


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.status = ListingStatus.archived
