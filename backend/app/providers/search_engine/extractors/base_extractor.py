"""
Base Extractor Interface

Abstract base class for modular job page content extractors in the extraction pipeline.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.providers.search_engine.base_search import SearchResult
from app.schemas.job import NormalizedJob


class BaseExtractor(ABC):
    """
    Abstract interface for specialized HTML page extractors.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique technical identifier for the extractor (e.g. 'json_ld', 'open_graph').
        """
        pass

    @abstractmethod
    async def extract(
        self,
        url: str,
        html: str,
        search_result: Optional[SearchResult] = None
    ) -> Optional[NormalizedJob]:
        """
        Attempts to extract a `NormalizedJob` from the provided page HTML content.

        Args:
            url: Target web page URL.
            html: HTML document content string.
            search_result: Optional SearchResult context item.

        Returns:
            `NormalizedJob` if extraction succeeded, or `None` if unhandled.
        """
        pass
