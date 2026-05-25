from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.inventory import PlatformListing, PlatformListingStatus, PriceHistory

router = APIRouter(prefix="/inventory", tags=["inventory"])


class PlatformListingCreate(BaseModel):
    listing_id: int
    platform: str
    list_price: float
    platform_fee: float = 0.0
    shipping_cost: float = 0.0
    net_profit: float = 0.0
    platform_listing_id: str | None = None
    url: str | None = None


class PlatformListingOut(BaseModel):
    id: int
    listing_id: int
    platform: str
    platform_listing_id: str | None
    url: str | None
    list_price: float
    platform_fee: float
    shipping_cost: float
    net_profit: float
    status: str
    listed_at: datetime | None
    sold_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PriceHistoryOut(BaseModel):
    id: int
    listing_id: int
    platform: str | None
    old_price: float
    new_price: float
    reason: str | None
    changed_at: datetime

    model_config = {"from_attributes": True}


@router.get("/listing/{listing_id}", response_model=list[PlatformListingOut])
async def get_platform_listings(listing_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlatformListing).where(PlatformListing.listing_id == listing_id)
    )
    return result.scalars().all()


@router.post("/", response_model=PlatformListingOut, status_code=status.HTTP_201_CREATED)
async def create_platform_listing(data: PlatformListingCreate, db: AsyncSession = Depends(get_db)):
    pl = PlatformListing(**data.model_dump())
    db.add(pl)
    await db.flush()
    await db.refresh(pl)
    return pl


@router.post("/{platform_listing_id}/sold", response_model=PlatformListingOut)
async def mark_platform_sold(platform_listing_id: int, db: AsyncSession = Depends(get_db)):
    pl = await db.get(PlatformListing, platform_listing_id)
    if not pl:
        raise HTTPException(status_code=404, detail="Platform listing not found")
    from datetime import timezone
    pl.status = PlatformListingStatus.sold
    pl.sold_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(pl)
    return pl


@router.get("/price-history/{listing_id}", response_model=list[PriceHistoryOut])
async def get_price_history(listing_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.listing_id == listing_id)
        .order_by(PriceHistory.changed_at.desc())
    )
    return result.scalars().all()


@router.post("/price-history", response_model=PriceHistoryOut, status_code=status.HTTP_201_CREATED)
async def record_price_change(
    listing_id: int,
    platform: str | None,
    old_price: float,
    new_price: float,
    reason: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    ph = PriceHistory(
        listing_id=listing_id,
        platform=platform,
        old_price=old_price,
        new_price=new_price,
        reason=reason,
    )
    db.add(ph)
    await db.flush()
    await db.refresh(ph)
    return ph
