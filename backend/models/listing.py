import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class ListingStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    sold = "sold"
    archived = "archived"


class Condition(str, enum.Enum):
    new = "new"
    like_new = "like_new"
    good = "good"
    fair = "fair"
    poor = "poor"


class Priority(str, enum.Enum):
    speed = "speed"
    price = "price"
    balanced = "balanced"


class ShippingPreference(str, enum.Enum):
    pickup_only = "pickup_only"
    shipping_only = "shipping_only"
    both = "both"


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(255))
    condition: Mapped[str | None] = mapped_column(Enum(Condition))
    condition_description: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list | None] = mapped_column(JSON)
    dimensions: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(Enum(ListingStatus), default=ListingStatus.draft)
    priority: Mapped[str] = mapped_column(Enum(Priority), default=Priority.balanced)
    shipping_preference: Mapped[str] = mapped_column(
        Enum(ShippingPreference), default=ShippingPreference.both
    )

    quantity: Mapped[int] = mapped_column(Integer, default=1)
    quantity_available: Mapped[int] = mapped_column(Integer, default=1)
    quantity_sold: Mapped[int] = mapped_column(Integer, default=0)

    photos: Mapped[list | None] = mapped_column(JSON)
    ai_analysis: Mapped[dict | None] = mapped_column(JSON)

    # Platform listing IDs set after posting
    ebay_listing_id: Mapped[str | None] = mapped_column(String(255))
    etsy_listing_id: Mapped[str | None] = mapped_column(String(255))

    # Per-item markdown rules (override user defaults)
    markdown_percent: Mapped[float | None] = mapped_column(Float)
    markdown_days: Mapped[int | None] = mapped_column(Integer)
    floor_price: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    listed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["UserProfile"] = relationship(back_populates="listings")  # noqa: F821
    platform_listings: Mapped[list["PlatformListing"]] = relationship(  # noqa: F821
        back_populates="listing", cascade="all, delete-orphan", lazy="selectin"
    )
    price_history: Mapped[list["PriceHistory"]] = relationship(  # noqa: F821
        back_populates="listing", cascade="all, delete-orphan", lazy="selectin"
    )
    notification_logs: Mapped[list["NotificationLog"]] = relationship(  # noqa: F821
        back_populates="listing", cascade="all, delete-orphan", lazy="selectin"
    )
