"""
Resume Schemas

Pydantic validation models for resume upload responses and detailed resume objects.
"""

from datetime import datetime
import uuid
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ParsedResumeData(BaseModel):
    """
    Structured fields extracted from resume text by AI.
    """
    full_name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    skills: List[str] = Field([], description="List of technical and soft skills")
    experience: List[Dict[str, Any]] = Field([], description="List of work experience entries")
    education: List[Dict[str, Any]] = Field([], description="List of education entries")
    projects: List[Dict[str, Any]] = Field([], description="List of projects")


class ResumeResponse(BaseModel):
    """
    Resume payload returned by API endpoints.
    """
    id: uuid.UUID
    filename: str
    file_path: str
    raw_text: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    is_active: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ResumeListResponse(BaseModel):
    """
    Wrapper list response for uploaded resumes.
    """
    total: int
    resumes: List[ResumeResponse]
