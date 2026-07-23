"""
Search Provider Interface & Data Contracts

Defines the core `SearchResult` payload and abstract `SearchProvider` interface.
Decouples search engine query execution from web page extraction.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SearchResult:
    """
    Normalized result entry returned by search engine providers.
    """
    title: str
    url: str
    snippet: str
    engine: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class SearchProvider(ABC):
    """
    Abstract interface for Search Engine Plugins (Google, Bing, Brave, Tavily, etc.).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique technical identifier for the search engine (e.g. 'google', 'bing').
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Human readable display name (e.g. 'Google Search', 'Bing Web Search').
        """
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """
        Indicates whether the search provider is configured and available for execution.
        """
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Executes web search for a target query and returns normalized SearchResult items.

        Args:
            query: Pre-formulated target search query string.
            limit: Maximum number of search results to return.

        Returns:
            List of `SearchResult` objects.
        """
        pass
