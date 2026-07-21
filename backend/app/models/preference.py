"""
Preference Model Definition

Defines the SQLAlchemy ORM model for storing user job search preferences.
Maps to the `preferences` table in PostgreSQL / SQLite.
"""

from datetime import datetime
import uuid
from typing import List, Optional, Any
from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base


class Preference(Base):
    """
    Preference Entity

    Stores user job search criteria: preferred roles, locations,
    salary range, work type (remote/hybrid/onsite), preferred target companies,
    and experience level.
    """
    __tablename__ = "preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for preference record"
    )

    preferred_roles: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="List of target job titles (e.g. ['Backend Engineer', 'Python Developer'])"
    )

    preferred_locations: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="List of target geographic locations (e.g. ['San Francisco, CA', 'Remote'])"
    )

    min_salary: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=100000,
        comment="Minimum acceptable annual salary in USD"
    )

    max_salary: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=180000,
        comment="Target maximum annual salary in USD"
    )

    work_type: Mapped[str] = mapped_column(
        String(50),
        default="remote",
        nullable=False,
        comment="Work location arrangement: 'remote', 'hybrid', or 'onsite'"
    )

    preferred_companies: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="List of target dream companies (e.g. ['Stripe', 'Notion', 'Figma'])"
    )

    experience_years: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="Years of professional experience"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Timestamp when preferences were last modified"
    )
