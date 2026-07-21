"""
Dashboard Schemas

Pydantic models for returning aggregated dashboard statistics and activity metrics.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.job import JobResponse


class RecentActivityItem(BaseModel):
    """
    Represents a single event or action in the activity feed.
    """
    id: str = Field(..., description="Unique event identifier")
    title: str = Field(..., description="Activity title")
    description: str = Field(..., description="Details regarding the event")
    timestamp: datetime = Field(..., description="When the activity occurred")
    type: str = Field(..., description="Event type: 'job_discovered', 'application_status', etc.")


class DashboardStatsResponse(BaseModel):
    """
    Payload containing aggregated application, job, and status counts for the dashboard.
    """
    total_jobs_found: int = Field(0, description="Total jobs discovered in database")
    saved_jobs_count: int = Field(0, description="Number of saved jobs")
    applied_count: int = Field(0, description="Total submitted applications")
    interviews_count: int = Field(0, description="Total interviews scheduled")
    offers_count: int = Field(0, description="Total job offers received")
    recent_jobs: List[JobResponse] = Field([], description="List of recently discovered job postings")
    recent_activities: List[RecentActivityItem] = Field([], description="Recent activity event log")
