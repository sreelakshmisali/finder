"""
Notification Schemas

Pydantic validation models for returning candidate notifications, unread counts, and pipeline responses.
"""

from datetime import datetime
import uuid
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.job import JobResponse


class NotificationResponse(BaseModel):
    """
    In-app notification payload returned by API endpoints.
    """
    id: uuid.UUID = Field(..., description="Unique notification ID")
    user_id: uuid.UUID = Field(..., description="Recipient candidate user ID")
    job_id: Optional[uuid.UUID] = Field(None, description="Associated job posting ID")
    type: str = Field(..., description="Category: 'high_match_job', 'saved_search_alert', etc.")
    title: str = Field(..., description="Notification header title")
    message: str = Field(..., description="Notification text description")
    read: bool = Field(..., description="Whether notification is marked as read")
    created_at: datetime = Field(..., description="Creation timestamp")
    job: Optional[JobResponse] = Field(None, description="Embedded job details payload")

    class Config:
        from_attributes = True


class NotificationUnreadCountResponse(BaseModel):
    """
    Unread notification count payload.
    """
    unread_count: int = Field(..., ge=0, description="Total unread notifications count")


class PipelineRunResponse(BaseModel):
    """
    Response payload for manually triggered notification pipeline run.
    """
    user_id: uuid.UUID
    saved_searches_processed: int
    jobs_evaluated: int
    new_notifications_created: int
    message: str
