"""
Resume Model Definition

Defines the SQLAlchemy ORM model for storing uploaded PDF resumes.
Maps to the `resumes` table in PostgreSQL.
"""

from datetime import datetime
import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Resume(Base):
    """
    Resume Entity

    Stores uploaded PDF file metadata, disk path, active state flag,
    and extracted parsed data (skills, experience, education).
    """
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the resume"
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of owning user account"
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original uploaded filename (e.g. 'John_Doe_Resume.pdf')"
    )

    file_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="Path on disk where PDF is saved"
    )

    raw_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Extracted raw plain text from PDF file"
    )

    parsed_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Structured JSON extracted by AI (skills, experience, education, projects)"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="True if this is the active resume used for job matching"
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when resume was uploaded"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resumes")
