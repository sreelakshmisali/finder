"""
Profile Setup Schemas

Pydantic validation models for combined candidate profile setup responses.
"""

from datetime import datetime
import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.schemas.preference import PreferenceResponse


class ResumeSummary(BaseModel):
    """
    Lightweight summary of candidate's active resume and parsed details.
    """
    has_resume: bool = Field(..., description="Whether active resume exists")
    filename: Optional[str] = Field(None, description="PDF filename")
    full_name: Optional[str] = Field(None, description="Extracted candidate name")
    email: Optional[str] = Field(None, description="Extracted candidate email")
    phone: Optional[str] = Field(None, description="Extracted candidate phone")
    skills: List[str] = Field([], description="Extracted technical and soft skills")
    roles: List[str] = Field([], description="Extracted target roles/titles from experience")
    experience: List[Dict[str, Any]] = Field([], description="Extracted work experience entries")
    uploaded_at: Optional[datetime] = Field(None, description="Upload timestamp")


class ProfileSetupResponse(BaseModel):
    """
    Combined Profile Setup response output.
    """
    resume_completed: bool = Field(..., description="True if active resume exists and is parsed")
    preferences_completed: bool = Field(..., description="True if search preferences are configured")
    profile_completion_percentage: float = Field(..., description="Overall profile completion percentage")
    resume_summary: Optional[ResumeSummary] = Field(None, description="Active resume summary")
    preferences: Optional[PreferenceResponse] = Field(None, description="User search preferences")
