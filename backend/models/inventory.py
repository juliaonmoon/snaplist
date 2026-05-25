import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Platform(str, enum.Enum):
    facebook = "facebook"
    kijiji = "kijiji"
    ebay = "ebay"
    craigslist = "craigslist"
    etsy = "etsy"


class PlatformListingStatus(str, enum.Enum):
    active = "active"
    sold = "sold"
    archived = "archived"


class PlatformListing(Base):
    """Tracks this listing on each individual resale platform."""

    __tablename__ = "platform_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), nullable=False)
    platform: Mapped[str] = mapped_column(Enum(Platform), nullable=False)
    platform_listing_id: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(Text)

    list_price: Mapped[float] = mapped_column(Float, nullable=False)
    platform_fee: Mapped[float] = mapped_column(Float, default=0.0)
    shipping_cost: Mapped[float] = mapped_column(Float, default=0.0)
    net_profit: Mapped[float] = mapped_column(Float, default=0.0)

    status: Mapped[str] = mapped_column(
        Enum(PlatformListingStatus), default=PlatformListingStatus.active
    )

    listed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    listing: Mapped["Listing"] = relationship(back_populates="platform_listings")  # noqa: F821


class PriceHistory(Base):
    """Audit trail for every price change on a listing."""

    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), nullable=False)
    platform: Mapped[str | None] = mapped_column(Enum(Platform))
    old_price: Mapped[float] = mapped_column(Float, nullable=False)
    new_price: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    listing: Mapped["Listing"] = relationship(back_populates="price_history")  # noqa: F821


class NotificationLog(Base):
    """Log of all notifications sent to the seller."""

    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int | None] = mapped_column(ForeignKey("listings.id"))
    notification_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), default="email")
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    listing: Mapped["Listing"] = relationship(back_populates="notification_logs")  # noqa: F821
