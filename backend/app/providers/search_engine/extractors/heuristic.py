"""
Heuristic & Search Result Fallback Extractor

Guarantees job normalization by deriving signals from SearchResult titles, snippets, and URL domain names.
"""

from urllib.parse import urlparse
import logging
from typing import Optional
from datetime import datetime

from app.providers.search_engine.base_search import SearchResult
from app.providers.search_engine.extractors.base_extractor import BaseExtractor
from app.schemas.job import NormalizedJob

logger = logging.getLogger(__name__)


class HeuristicExtractor(BaseExtractor):
    """
    Fallback extractor using SearchResult data.
    """

    @property
    def name(self) -> str:
        return "heuristic"

    async def extract(
        self,
        url: str,
        html: str,
        search_result: Optional[SearchResult] = None
    ) -> Optional[NormalizedJob]:
        if not search_result and not url:
            return None

        title = search_result.title if search_result else "Software Position"
        snippet = search_result.snippet if search_result else f"Opportunity at {url}"

        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace("www.", "")
        company = domain.split(".")[0].capitalize() if domain else "Technology Company"

        is_remote = "remote" in title.lower() or "remote" in snippet.lower()

        return NormalizedJob(
            company=company,
            title=title,
            location="Remote" if is_remote else "Onsite",
            remote=is_remote,
            salary=None,
            description=snippet,
            url=url,
            source="search_engine",
            posted_date=datetime.utcnow()
        )
