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


class ResumeQualityAnalysisResponse(BaseModel):
    """
    Response payload for general resume quality analysis (missing skills, weak descriptions, ATS issues).
    """
    quality_score: float = Field(..., description="Overall resume quality score (0 to 100)")
    missing_skills: List[str] = Field(default_factory=list, description="Missing industry standard tech skills")
    weak_descriptions: List[str] = Field(default_factory=list, description="Weak descriptions & passive phrasing recommendations")
    ats_issues: List[str] = Field(default_factory=list, description="ATS formatting and structural compliance warnings")
    summary: str = Field(..., description="Executive summary of resume quality audit")


class JobSpecificSuggestionsRequest(BaseModel):
    """
    Request payload for job-specific resume improvement recommendations.
    """
    job_id: Optional[uuid.UUID] = Field(None, description="Optional target job ID from Finder database")
    job_title: Optional[str] = Field(None, description="Optional target job title (e.g. 'Senior Python Developer')")
    job_description: Optional[str] = Field(None, description="Optional raw text of job description")


class JobSpecificSuggestionsResponse(BaseModel):
    """
    Response payload for job-specific resume recommendations.
    """
    job_title: Optional[str] = Field(None, description="Target position title")
    matching_skills: List[str] = Field(default_factory=list, description="Skills present in both resume and job posting")
    missing_job_skills: List[str] = Field(default_factory=list, description="Required skills missing from candidate resume")
    suggested_changes: List[str] = Field(default_factory=list, description="Actionable bullet point improvement suggestions")
    tailored_summary: str = Field(..., description="Executive advice for tailoring resume to target job")
