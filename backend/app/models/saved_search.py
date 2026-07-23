"""
Saved Search Model Definition

Defines the SQLAlchemy ORM model for storing candidate saved job discovery searches and filter rules.
Maps to the `saved_searches` table in PostgreSQL / SQLite.
"""

from datetime import datetime
import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class SavedSearch(Base):
    """
    SavedSearch Entity

    Stores user job search rules including query terms, filter criteria,
    creation date, and last execution timestamp.
    """
    __tablename__ = "saved_searches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for saved search entry"
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of owning user account"
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Human-readable title for the search rule (e.g. 'Python Remote Jobs')"
    )

    query: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Keyword search string (e.g. 'Python Backend')"
    )

    filters: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="Filter rules dictionary (location, remote_only, sources, min_salary, etc.)"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when search rule was saved"
    )

    last_run: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Timestamp when search rule was last executed"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="saved_searches")
