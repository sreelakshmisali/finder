"""
Job Discovery Provider Architecture

Defines the core discovery interface (`JobDiscoveryProvider`), strongly-typed taxonomy Enum (`ProviderType`),
execution context (`DiscoveryContext`), and specialized abstract base classes:
- ATSProvider (Greenhouse, Lever, Ashby, Workday)
- SearchEngineProvider (Google, Bing, Serper)
- CrawlerProvider (Career Page Web Crawlers)
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
import uuid
from typing import List, Optional, Dict, Any

from app.schemas.job import JobSearchQuery, NormalizedJob


class ProviderType(str, Enum):
    """
    Strongly-typed taxonomy for job discovery providers.
    """
    ATS = "ats"
    SEARCH_ENGINE = "search_engine"
    CRAWLER = "crawler"


@dataclass
class DiscoveryContext:
    """
    Richer context wrapper passed to job discovery providers.
    Allows future search engines or web crawlers to receive user signals,
    filter rules, or custom execution parameters without altering provider method signatures.
    """
    query: JobSearchQuery
    user_id: Optional[uuid.UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class JobDiscoveryProvider(ABC):
    """
    Abstract Base Class for all Job Discovery Providers.

    Every provider is responsible for searching/discovering job postings
    and returning standardized `NormalizedJob` objects.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        Unique technical identifier (e.g. 'greenhouse', 'lever', 'ashby', 'google_search').
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Human friendly name (e.g. 'Greenhouse Board', 'Lever ATS', 'Google Jobs').
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Brief summary description of what this discovery provider queries.
        """
        pass

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """
        Strongly typed category of the provider (ATS, SEARCH_ENGINE, or CRAWLER).
        """
        pass

    @abstractmethod
    async def discover(self, context: DiscoveryContext) -> List[NormalizedJob]:
        """
        Executes discovery matching the provided context and returns normalized jobs.

        Args:
            context: `DiscoveryContext` containing query parameters, user ID, and metadata.

        Returns:
            List of `NormalizedJob` instances.
        """
        pass

    @abstractmethod
    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        """
        Fetches full details for a single job posting URL.
        """
        pass


class ATSProvider(JobDiscoveryProvider):
    """
    Abstract base class for Applicant Tracking System (ATS) providers.
    """

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.ATS


class SearchEngineProvider(JobDiscoveryProvider):
    """
    Abstract base class for Web Search Engine discovery providers (Google, Bing, etc.).
    """

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.SEARCH_ENGINE


class CrawlerProvider(JobDiscoveryProvider):
    """
    Abstract base class for direct career page web crawlers.
    """

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.CRAWLER
