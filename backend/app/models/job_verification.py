"""
Job Verification Model Definition

This module defines the SQLAlchemy ORM model for job verification status.
It represents the `job_verifications` table in the PostgreSQL database.
"""

from datetime import datetime
import uuid
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base


class JobVerification(Base):
    """
    Job Verification Entity

    Stores the latest verification status of a job posting.
    Supports a one-to-one relationship with the Job entity.
    """
    __tablename__ = "job_verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the verification record"
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Foreign key to the jobs table"
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVE",
        index=True,
        comment="Verification status: ACTIVE, EXPIRED, FAILED"
    )

    last_checked: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the job was last checked"
    )

    next_check_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When the job should be checked next"
    )

    verification_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of consecutive verification attempts"
    )

    failure_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for failure or expiration (e.g. 'HTTP 404', 'Position filled')"
    )

    # Relationship
    job = relationship("Job", back_populates="verification")
