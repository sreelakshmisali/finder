"""
Application & ApplicationLog Models Definition

Defines the SQLAlchemy ORM models for tracking job applications and their audit trail history.
Maps to `applications` and `application_logs` tables in PostgreSQL / SQLite.
"""

from datetime import datetime
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base


class Application(Base):
    """
    Application Entity

    Tracks a user's intent or progress for a specific job posting.
    Statuses follow a state machine:
    saved -> approved -> queued -> running -> awaiting_input -> awaiting_confirmation -> completed / failed -> interview / rejected / offer
    """
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the application"
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of the associated job posting"
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="saved",
        nullable=False,
        index=True,
        comment="Application status code (e.g. 'saved', 'approved', 'completed', 'interview')"
    )

    match_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Match score percentage snapshot when application was created"
    )

    match_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Snapshot of AI match explanation payload"
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User notes (e.g. interview preparation, referral details)"
    )

    applied_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when application submission was confirmed"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when record was created"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Timestamp when record was last updated"
    )

    # Relationships
    job: Mapped["Job"] = relationship("Job", lazy="joined")
    logs: Mapped[List["ApplicationLog"]] = relationship(
        "ApplicationLog",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationLog.created_at.desc()"
    )


class ApplicationLog(Base):
    """
    ApplicationLog Entity

    Audit log history tracking status changes and automation events for an application.
    """
    __tablename__ = "application_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique log entry identifier"
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of parent application"
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Action summary (e.g. 'Status Changed', 'Automation Started')"
    )

    old_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Previous status string before transition"
    )

    new_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="New status string after transition"
    )

    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed explanation or log output"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when audit log entry was created"
    )

    # Relationship
    application: Mapped["Application"] = relationship("Application", back_populates="logs")
