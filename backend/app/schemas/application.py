"""
Application Schemas

Pydantic validation models for creating applications, updating statuses, notes, and building API responses.
"""

from datetime import datetime
import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.schemas.job import JobResponse


class ApplicationCreate(BaseModel):
    """
    Payload for creating or bookmarking a job application.
    """
    job_id: uuid.UUID = Field(..., description="ID of the target job posting")
    status: str = Field("saved", description="Initial status ('saved' or 'approved')")
    notes: Optional[str] = Field(None, description="Optional user notes")


class ApplicationUpdateStatus(BaseModel):
    """
    Payload for transitioning an application's status.
    """
    status: str = Field(..., description="New status string")
    details: Optional[str] = Field(None, description="Optional transition note or audit explanation")


class ApplicationUpdateNotes(BaseModel):
    """
    Payload for updating application user notes.
    """
    notes: str = Field(..., description="Updated user notes")


class ApplicationLogResponse(BaseModel):
    """
    Audit log item response schema.
    """
    id: uuid.UUID
    application_id: uuid.UUID
    action: str
    old_status: Optional[str] = None
    new_status: str
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationResponse(BaseModel):
    """
    Application full payload response schema.
    """
    id: uuid.UUID
    job_id: uuid.UUID
    status: str
    match_score: Optional[float] = None
    match_details: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    applied_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    job: JobResponse
    logs: List[ApplicationLogResponse] = []

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    """
    List wrapper response for applications.
    """
    total: int = Field(..., description="Total applications count")
    applications: List[ApplicationResponse] = Field(..., description="List of applications")
