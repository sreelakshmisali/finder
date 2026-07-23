"""
Classification Schemas

Data contracts for job page taxonomy and classification results.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PageType(str, Enum):
    """
    Taxonomy for web page classification in the job discovery pipeline.
    """
    JOB_POSTING = "JOB_POSTING"       # Single specific job opportunity
    CAREER_PAGE = "CAREER_PAGE"       # General company career portal index/search
    COMPANY_PAGE = "COMPANY_PAGE"     # General company landing/about page
    IRRELEVANT = "IRRELEVANT"         # Blog post, news, press release, dead link, etc.


class ClassificationResult(BaseModel):
    """
    Structured result of a page classification pass.
    """
    page_type: PageType = Field(..., description="The inferred type of the page")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the classification")
    matched_signals: List[str] = Field(default_factory=list, description="List of rule/signal names that matched positively")
    failed_signals: List[str] = Field(default_factory=list, description="List of rule/signal names that failed to match")
    is_valid_job: bool = Field(..., description="True only if page is JOB_POSTING and confidence >= threshold")
    rejected_reason: Optional[str] = Field(None, description="Reason if page was rejected (e.g., negative signals dominant)")
