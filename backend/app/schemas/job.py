"""
Job Schemas

Pydantic validation models for job search queries, normalized job structures,
and API response payloads.
"""

from datetime import datetime
import uuid
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class JobSearchQuery(BaseModel):
    """
    Search parameters sent by the client or service.

    Allows filtering by keywords, location, remote preference, and specific providers.
    """
    query: Optional[str] = Field(None, description="Search keyword (e.g. 'Python', 'Software Engineer')")
    location: Optional[str] = Field(None, description="Preferred location (e.g. 'San Francisco', 'Remote')")
    remote_only: bool = Field(False, description="Filter to remote positions only")
    providers: Optional[List[str]] = Field(None, description="Specific providers to query (e.g. ['greenhouse', 'lever'])")
    limit: int = Field(50, ge=1, le=200, description="Maximum number of results to return")
    manual_search: bool = Field(False, description="Whether user explicitly supplied search overrides")
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
    last_verified_date: Optional[datetime] = Field(default_factory=datetime.utcnow, description="When this job was last verified as active")


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
    posted_date: datetime
    fetched_at: datetime
    last_verified_date: datetime
    content_hash: str

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """
    Paginated/aggregated job search response list wrapper.
    """
    total: int = Field(..., description="Total number of unique jobs returned")
    jobs: List[JobResponse] = Field(..., description="List of normalized jobs")
    providers_searched: List[str] = Field(..., description="List of providers queried")
    suggested_queries: List[str] = Field(default=[], description="Generated candidate-aware search suggestions")
    is_generated: bool = Field(False, description="Whether search query was auto-generated from resume")
    applied_query: Optional[str] = Field(None, description="The actual search query string executed")
    applied_location: Optional[str] = Field(None, description="The actual location parameter executed")


class ProviderInfo(BaseModel):
    """
    Metadata about an available job discovery provider.
    """
    name: str = Field(..., description="Identifier name (e.g., 'greenhouse')")
    display_name: str = Field(..., description="Human friendly title (e.g., 'Greenhouse')")
    description: str = Field(..., description="Brief description of the source")
    enabled: bool = Field(True, description="Whether this provider is currently active")
