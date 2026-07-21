"""
Match Schemas

Pydantic validation models for job matching requests and AI match output responses.
"""

from typing import List, Optional, Dict, Any
import uuid
from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    """
    Request payload to calculate match score for a single job.
    """
    job_id: uuid.UUID = Field(..., description="ID of the job to evaluate")
    resume_id: Optional[uuid.UUID] = Field(None, description="Optional resume ID (defaults to active resume)")


class BatchMatchRequest(BaseModel):
    """
    Request payload to batch match multiple jobs.
    """
    job_ids: List[uuid.UUID] = Field(..., description="List of job IDs to evaluate")
    resume_id: Optional[uuid.UUID] = Field(None, description="Optional resume ID (defaults to active resume)")


class MatchResult(BaseModel):
    """
    Result payload containing calculated match score and AI explanation.
    """
    job_id: uuid.UUID = Field(..., description="Evaluated job ID")
    score: float = Field(..., ge=0.0, le=100.0, description="Match score percentage (0-100%)")
    reasons: List[str] = Field(default=[], description="List of positive matching reasons")
    missing_skills: List[str] = Field(default=[], description="Required skills missing from candidate resume")
    recommendation: str = Field(..., description="Overall AI recommendation summary")
    score_breakdown: Optional[Dict[str, float]] = Field(None, description="Raw breakdown of keyword and preference scores")


class BatchMatchResult(BaseModel):
    """
    Wrapper payload for batch matching output.
    """
    matches: List[MatchResult] = Field(..., description="List of match results")
