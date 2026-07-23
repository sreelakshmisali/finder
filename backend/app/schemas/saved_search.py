"""
Saved Search Schemas

Pydantic validation models for creating, updating, and returning saved search rule entries.
"""

from datetime import datetime
import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SavedSearchCreate(BaseModel):
    """
    Payload for creating a new saved search rule.
    """
    name: str = Field(..., max_length=150, description="Name for the search rule (e.g. 'Python Remote Jobs')")
    query: Optional[str] = Field(None, max_length=255, description="Search keyword terms (e.g. 'Python Backend')")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Filter rules (location, remote_only, sources, min_salary, etc.)")


class SavedSearchResponse(BaseModel):
    """
    Saved search entry payload returned by API endpoints.
    """
    id: uuid.UUID = Field(..., description="Unique saved search ID")
    user_id: uuid.UUID = Field(..., description="ID of owning candidate user")
    name: str = Field(..., description="Name for the search rule")
    query: Optional[str] = Field(None, description="Search keyword string")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filter rules dictionary")
    created_at: datetime = Field(..., description="Timestamp when search rule was saved")
    last_run: Optional[datetime] = Field(None, description="Timestamp when search rule was last executed")

    class Config:
        from_attributes = True
