"""
Search Profile & Intent Schemas

Data contracts for the decoupled Resume Search Profile and Search Intent Engine.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ResumeSearchProfile(BaseModel):
    """
    Normalized intermediate representation extracted from a candidate's resume data.
    """
    skills: List[str] = Field(default_factory=list, description="All technical and soft skills")
    primary_languages: List[str] = Field(default_factory=list, description="Core programming languages (e.g. Python, Java)")
    frameworks: List[str] = Field(default_factory=list, description="Frameworks and libraries (e.g. Django, FastAPI, React)")
    databases: List[str] = Field(default_factory=list, description="Databases & storage engines (e.g. PostgreSQL, Redis)")
    roles: List[str] = Field(default_factory=list, description="Extracted previous job titles/roles")
    experience_level: str = Field("Mid", description="Seniority level (Junior, Mid, Senior, Lead, Executive)")
    years_experience: Optional[int] = Field(None, description="Calculated or explicitly stated total years of work experience")
    domains: List[str] = Field(default_factory=list, description="Inferred domain expertise (Backend, Frontend, Full Stack, Data, DevOps, Mobile)")


class GeneratedQuery(BaseModel):
    """
    Structured search query string enriched with priority weight and generation strategy metadata.
    """
    query: str = Field(..., description="Target search query string (e.g. 'Python Backend Engineer')")
    priority: int = Field(..., description="Query relevance priority score (higher numbers indicate stronger relevance)")
    strategy: str = Field(..., description="Generation strategy descriptor (e.g. 'tech_domain_role', 'framework_role')")
