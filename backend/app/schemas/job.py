"""
Job Schemas

Pydantic validation models for job search queries, normalized job structures,
and API response payloads.
"""

from datetime import datetime
import uuid
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl

class SearchMode(str, Enum):
    NORMAL = "NORMAL"
    SMART = "SMART"



class JobSearchQuery(BaseModel):
    """
    Search parameters sent by the client or service.

    Allows filtering by keywords, location, and remote preference.
    """
    query: Optional[str] = Field(None, description="Search keyword (e.g. 'Python', 'Software Engineer')")
    location: Optional[str] = Field(None, description="Preferred location (e.g. 'San Francisco', 'Remote')")
    remote_only: bool = Field(False, description="Filter to remote positions only")
    limit: int = Field(50, ge=1, le=200, description="Maximum number of results to return")
    search_mode: SearchMode = Field(default=SearchMode.NORMAL, description="The search mode to execute (NORMAL or SMART)")
    min_salary: Optional[int] = Field(None, description="Minimum salary filter")
    force_refresh: bool = Field(False, description="Bypass search cache and force fresh provider query")


class NormalizedJob(BaseModel):
    """
    Standardized job payload produced by all job providers.

    Every provider (Greenhouse, Lever, Ashby, etc.) translates its raw API
    response into this common structure before saving or displaying.
    """
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    location: str = Field("Remote", description="Location string")
    remote: bool = Field(True, description="Whether position is remote")
    salary: Optional[str] = Field(None, description="Salary range string")
    description: str = Field(..., description="Job description text")
    url: str = Field(..., description="Application URL")
    source: str = Field(..., description="Provider source identifier")
    posted_date: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Original posting date")
    required_skills: List[str] = Field(default_factory=list, description="Extracted required technical skills")
    apply_url: Optional[str] = Field(None, description="Direct application form link")
    can_apply: bool = Field(False, description="True if the job has an external application URL")
    last_verified_date: Optional[datetime] = Field(default_factory=datetime.utcnow, description="When this job was last verified as active")
    relevance_score: Optional[int] = Field(None, description="Score assigned by RelevanceRankingService")
    match_reasons: List[str] = Field(default_factory=list, description="Reasons for the relevance score")


class JobResponse(BaseModel):
    """
    Job payload returned by API endpoints. Matches database output format.
    """
    id: uuid.UUID
    company: str
    title: str
    location: str
    remote: bool
    salary: Optional[str] = None
    description: str
    url: str
    source: str
    apply_url: Optional[str] = None
    can_apply: bool = False
    posted_date: datetime
    fetched_at: datetime
    last_verified_date: datetime
    content_hash: str
    relevance_score: Optional[int] = None
    match_reasons: List[str] = []

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """
    Paginated/aggregated job search response list wrapper.
    """
    total: int = Field(..., description="Total number of unique jobs returned")
    jobs: List[JobResponse] = Field(..., description="List of normalized jobs")
    suggested_queries: List[str] = Field(default=[], description="Generated candidate-aware search suggestions")
    search_mode: SearchMode = Field(default=SearchMode.NORMAL, description="The search mode that was executed")
    applied_query: Optional[str] = Field(None, description="The actual search query string executed")
    applied_location: Optional[str] = Field(None, description="The actual location parameter executed")
