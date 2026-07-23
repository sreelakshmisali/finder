"""
Notification Model Definition

Defines the SQLAlchemy ORM model for candidate in-app notifications and job match alerts.
Maps to the `notifications` table in PostgreSQL / SQLite.
"""

from datetime import datetime
import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.job import Job


class Notification(Base):
    """
    Notification Entity

    Stores candidate in-app alert notifications regarding new high-matching jobs,
    application status updates, and pipeline events.
    """
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique notification identifier"
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of candidate user recipient"
    )

    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Associated job posting ID (if applicable)"
    )

    type: Mapped[str] = mapped_column(
        String(50),
        default="high_match_job",
        nullable=False,
        comment="Notification category: 'high_match_job', 'saved_search_alert', 'application_update'"
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Notification title header"
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Notification body text description"
    )

    read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether candidate has marked notification as read"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when notification was created"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    job: Mapped[Optional["Job"]] = relationship("Job")
