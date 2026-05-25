from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user_profile import UserProfile

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileCreate(BaseModel):
    name: str
    email: str
    location: str | None = None
    pickup_location: str | None = None
    default_priority: str = "balanced"
    default_shipping_preference: str = "both"
    default_markdown_percent: float = 10.0
    default_markdown_days: int = 14
    default_floor_price: float = 0.0
    notification_email: str | None = None
    pushover_key: str | None = None


class ProfileUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    pickup_location: str | None = None
    default_priority: str | None = None
    default_shipping_preference: str | None = None
    default_markdown_percent: float | None = None
    default_markdown_days: int | None = None
    default_floor_price: float | None = None
    notification_email: str | None = None
    pushover_key: str | None = None


class ProfileOut(BaseModel):
    id: int
    name: str
    email: str
    location: str | None
    pickup_location: str | None
    default_priority: str
    default_shipping_preference: str
    default_markdown_percent: float
    default_markdown_days: int
    default_floor_price: float
    notification_email: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.post("/", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
async def create_profile(data: ProfileCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(UserProfile).where(UserProfile.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    profile = UserProfile(**data.model_dump())
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=ProfileOut)
async def get_profile(profile_id: int, db: AsyncSession = Depends(get_db)):
    profile = await db.get(UserProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/{profile_id}", response_model=ProfileOut)
async def update_profile(
    profile_id: int, data: ProfileUpdate, db: AsyncSession = Depends(get_db)
):
    profile = await db.get(UserProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(profile, field, value)
    await db.flush()
    await db.refresh(profile)
    return profile
