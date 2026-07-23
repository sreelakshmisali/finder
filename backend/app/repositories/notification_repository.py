"""
Notification Repository

Data access layer for Notification entities using SQLAlchemy AsyncSession.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    """
    Database queries for Notification objects.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: uuid.UUID,
        title: str,
        message: str,
        job_id: Optional[uuid.UUID] = None,
        notification_type: str = "high_match_job"
    ) -> Notification:
        """
        Creates and persists a new in-app notification.
        """
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            job_id=job_id,
            type=notification_type,
            title=title.strip(),
            message=message.strip(),
            read=False,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def notification_exists(self, user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
        """
        Checks if a notification for a specific job already exists for the user.
        Prevents duplicate alerts.
        """
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                and_(Notification.user_id == user_id, Notification.job_id == job_id)
            )
        )
        return (result.scalar() or 0) > 0

    async def get_user_notifications(self, user_id: uuid.UUID, limit: int = 50) -> List[Notification]:
        """
        Retrieves in-app notifications for user ordered by created_at desc.
        """
        result = await self.db.execute(
            select(Notification)
            .options(selectinload(Notification.job))
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """
        Calculates total unread notifications count for user.
        """
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                and_(Notification.user_id == user_id, Notification.read == False)
            )
        )
        return result.scalar() or 0

    async def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Notification]:
        """
        Marks a specific notification as read.
        """
        result = await self.db.execute(
            select(Notification).where(
                and_(Notification.id == notification_id, Notification.user_id == user_id)
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return None

        notification.read = True
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """
        Marks all notifications as read for a user. Returns count updated.
        """
        notifications = await self.get_user_notifications(user_id, limit=200)
        count = 0
        for n in notifications:
            if not n.read:
                n.read = True
                count += 1

        if count > 0:
            await self.db.commit()
        return count

    async def delete_notification(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Deletes a notification by ID.
        """
        result = await self.db.execute(
            select(Notification).where(
                and_(Notification.id == notification_id, Notification.user_id == user_id)
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return False

        await self.db.delete(notification)
        await self.db.commit()
        return True
