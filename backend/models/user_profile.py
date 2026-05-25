import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class DefaultPriority(str, enum.Enum):
    speed = "speed"
    price = "price"
    balanced = "balanced"


class ShippingPreference(str, enum.Enum):
    pickup_only = "pickup_only"
    shipping_only = "shipping_only"
    both = "both"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    pickup_location: Mapped[str | None] = mapped_column(Text)

    default_priority: Mapped[str] = mapped_column(
        Enum(DefaultPriority), default=DefaultPriority.balanced
    )
    default_shipping_preference: Mapped[str] = mapped_column(
        Enum(ShippingPreference), default=ShippingPreference.both
    )
    default_markdown_percent: Mapped[float] = mapped_column(Float, default=10.0)
    default_markdown_days: Mapped[int] = mapped_column(Integer, default=14)
    default_floor_price: Mapped[float] = mapped_column(Float, default=0.0)

    notification_email: Mapped[str | None] = mapped_column(String(255))
    pushover_key: Mapped[str | None] = mapped_column(String(255))

    # Encrypted OAuth tokens stored as strings (encrypted at rest via env/vault)
    ebay_oauth_token: Mapped[str | None] = mapped_column(Text)
    etsy_access_token: Mapped[str | None] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    listings: Mapped[list["Listing"]] = relationship(back_populates="user", lazy="selectin")  # noqa: F821
