from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.inventory import NotificationLog

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: int
    listing_id: int | None
    notification_type: str
    message: str
    channel: str
    sent_at: datetime
    read_at: datetime | None

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[NotificationOut])
async def get_notifications(unread_only: bool = False, db: AsyncSession = Depends(get_db)):
    q = select(NotificationLog).order_by(NotificationLog.sent_at.desc())
    if unread_only:
        q = q.where(NotificationLog.read_at.is_(None))
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(notification_id: int, db: AsyncSession = Depends(get_db)):
    from datetime import timezone
    n = await db.get(NotificationLog, notification_id)
    if n and not n.read_at:
        n.read_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(n)
    return n
