"""
Classification Schemas

Data contracts for job page taxonomy and classification results.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PageType(str, Enum):
    """
    Extended taxonomy for web page classification in the multi-stage job discovery pipeline.
    """
    JOB_POSTING = "JOB_POSTING"             # Single specific job opportunity → pass to JobExtractor
    ATS_CAREER_PAGE = "ATS_CAREER_PAGE"     # Greenhouse/Lever/Ashby/Workday listing → ATSLinkExtractor
    JOB_LISTING_PAGE = "JOB_LISTING_PAGE"   # Generic job listing/search page → JobLinkExtractor
    COMPANY_CAREERS_HOME = "COMPANY_CAREERS_HOME"  # Company /careers root → JobLinkExtractor
    JOB_BOARD = "JOB_BOARD"                 # Indeed/LinkedIn/Naukri → JobLinkExtractor
    BLOG = "BLOG"                           # Blog post → discard
    DOCUMENTATION = "DOCUMENTATION"         # Docs/wiki → discard
    HOME_PAGE = "HOME_PAGE"                 # Generic homepage → discard
    # Legacy values kept for backward compat with RuleBasedJobPageClassifier
    CAREER_PAGE = "CAREER_PAGE"             # Alias for COMPANY_CAREERS_HOME (legacy)
    COMPANY_PAGE = "COMPANY_PAGE"           # Generic company page (legacy)
    IRRELEVANT = "IRRELEVANT"               # Anything else → discard


class ClassificationResult(BaseModel):
    """
    Structured result of a page classification pass.
    """
    page_type: PageType = Field(..., description="The inferred type of the page")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the classification")
    matched_signals: List[str] = Field(default_factory=list, description="List of rule/signal names that matched positively")
    failed_signals: List[str] = Field(default_factory=list, description="List of rule/signal names that failed to match")
    is_valid_job: bool = Field(..., description="True only if page is JOB_POSTING and confidence >= threshold")
    rejected_reason: Optional[str] = Field(None, description="Reason if page was rejected")
    sub_type: Optional[str] = Field(None, description="Detected ATS platform name (e.g. 'greenhouse', 'lever', 'ashby') or job board name")
