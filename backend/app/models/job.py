"""
Job Model Definition

This module defines the SQLAlchemy ORM model for jobs.
It represents the `jobs` table in the PostgreSQL database.
All jobs discovered from different sources (Greenhouse, Lever, Ashby, etc.)
are normalized into this single schema.
"""

from datetime import datetime
import uuid
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base


class Job(Base):
    """
    Job Entity

    Stores normalized job posting details collected from various job boards.
    Each job has a unique URL and a content hash used for duplicate detection.
    """
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the job"
    )

    company: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Company name offering the position"
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Job title or role name"
    )

    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Remote",
        comment="Location string (e.g., 'San Francisco, CA' or 'Remote')"
    )

    remote: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="True if the position allows remote work"
    )

    salary: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Salary range or note (e.g., '$120,000 - $150,000' or None if unlisted)"
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full job description text"
    )

    url: Mapped[str] = mapped_column(
        String(1024),
        unique=True,
        nullable=False,
        index=True,
        comment="Direct application or job listing URL"
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Source provider name (e.g., 'greenhouse', 'lever', 'ashby')"
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA256 hash of company+title+location used for duplicate detection"
    )

    posted_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="When the job was originally posted or fetched"
    )

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="When Finder discovered this job listing"
    )

    last_verified_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="When this job was last verified as active"
    )

    # Relationships
    verification = relationship("JobVerification", back_populates="job", uselist=False, cascade="all, delete-orphan")

