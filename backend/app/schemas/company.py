"""
Company Discovery Schemas

Data contracts for company discovery results, search queries, and response payloads.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class DiscoveredCompany(BaseModel):
    """
    Normalized company entity discovered via search providers and career portal analysis.
    """
    name: str = Field(..., description="Company name (e.g. 'Hasura', 'Stripe')")
    career_url: str = Field(..., description="Absolute URL to company career portal or jobs page")
    industry: Optional[str] = Field("Technology", description="Inferred industry classification (e.g. 'Fintech', 'AI/ML', 'Developer Tools')")
    technology_tags: List[str] = Field(default_factory=list, description="Extracted tech stack keywords (e.g. ['Python', 'Django', 'PostgreSQL'])")
    website: Optional[str] = Field(None, description="Main company website domain or URL")
    headquarters: Optional[str] = Field(None, description="Headquarters location if available")
    company_size: Optional[str] = Field(None, description="Estimated company size category")
    confidence_score: float = Field(0.90, description="Discovery confidence score between 0.0 and 1.0")
    discovery_source: str = Field("search_engine", description="Source provider identifier")


class CompanySearchQuery(BaseModel):
    """
    Search parameters sent for company career discovery.
    """
    query: str = Field(..., description="Target search query (e.g. 'Python startups India', 'AI companies careers')")
    industry: Optional[str] = Field(None, description="Optional industry filter")
    location: Optional[str] = Field(None, description="Optional location/country filter")
    technology: Optional[str] = Field(None, description="Optional technology stack filter")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of companies to return")


class CompanyDiscoveryResponse(BaseModel):
    """
    API Response wrapper for company career discovery.
    """
    total: int = Field(..., description="Total number of unique companies discovered")
    companies: List[DiscoveredCompany] = Field(..., description="List of discovered companies")
    query_executed: str = Field(..., description="The query string executed")
