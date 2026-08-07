"""
Tagged URL Schema

Enriched URL container carrying scheduling metadata and search context.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.search_aggregator import SearchResult


@dataclass
class TaggedURL:
    """Enriched URL container carrying scheduling metadata and search context."""
    url: str
    provider: str                      # e.g., 'greenhouse', 'linkedin', 'company_career'
    company: Optional[str] = None     # Extracted company name
    priority_score: float = 0.0       # Score inherited from CandidateScorer
    source_page: Optional[str] = None # Parent listing page URL
    search_result: Optional[SearchResult] = None  # Strongly typed parent SearchResult context
    original_linkedin_url: Optional[str] = None
