"""
User Model Definition

Defines the SQLAlchemy ORM model for application users.
Maps to the `users` table in PostgreSQL / SQLite.
"""

from datetime import datetime
import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.resume import Resume
    from app.models.preference import Preference
    from app.models.application import Application


class User(Base):
    """
    User Entity

    Stores user account credentials, full name, email, hashed password, and status.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique user account identifier"
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address used for login"
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="User full name"
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Argon2 hashed password string"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether user account is active"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when user registered"
    )

    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when user last logged in"
    )

    # Relationships (passive_deletes=True allows DB ON DELETE CASCADE to handle child deletion)
    resumes: Mapped[List["Resume"]] = relationship(
        "Resume",
        back_populates="user",
        passive_deletes=True
    )
    preferences: Mapped[Optional["Preference"]] = relationship(
        "Preference",
        back_populates="user",
        passive_deletes=True,
        uselist=False
    )
    if TYPE_CHECKING:
        from app.models.saved_search import SavedSearch
        from app.models.notification import Notification

    applications: Mapped[List["Application"]] = relationship(
        "Application",
        back_populates="user",
        passive_deletes=True
    )
    saved_searches: Mapped[List["SavedSearch"]] = relationship(
        "SavedSearch",
        back_populates="user",
        passive_deletes=True
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        passive_deletes=True
    )
