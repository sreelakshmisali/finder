"""
Preference Schemas

Pydantic validation models for user preferences request payloads and response outputs.
"""

from datetime import datetime
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class PreferenceUpdate(BaseModel):
    """
    Payload for creating or updating user preferences.
    """
    preferred_roles: List[str] = Field(default=[], description="Target job titles")
    preferred_locations: List[str] = Field(default=[], description="Target locations")
    min_salary: Optional[int] = Field(100000, ge=0, description="Minimum annual salary USD")
    max_salary: Optional[int] = Field(180000, ge=0, description="Target maximum annual salary USD")
    work_type: str = Field("remote", description="Work type: 'remote', 'hybrid', or 'onsite'")
    preferred_companies: List[str] = Field(default=[], description="Target companies")
    experience_years: int = Field(3, ge=0, le=50, description="Years of experience")


class PreferenceResponse(BaseModel):
    """
    Preference response model output.
    """
    id: uuid.UUID
    preferred_roles: List[str]
    preferred_locations: List[str]
    min_salary: Optional[int]
    max_salary: Optional[int]
    work_type: str
    preferred_companies: List[str]
    experience_years: int
    updated_at: datetime

    class Config:
        from_attributes = True
