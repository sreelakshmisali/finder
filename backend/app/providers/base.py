"""
Abstract Job Provider Base Class

Defines the contract/interface that every job provider (Greenhouse, Lever, Ashby, etc.)
must implement.

Designing as a plugin architecture allows adding a new job board simply by:
1. Creating a new subclass of `JobProvider`.
2. Implementing `search()` and `get_details()`.
3. Registering it in `providers/registry.py`.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.schemas.job import JobSearchQuery, NormalizedJob


class JobProvider(ABC):
    """
    Abstract Base Class for Job Providers.

    Every provider is responsible for searching its external source
    and normalizing results into standard `NormalizedJob` objects.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        Unique technical identifier for the provider (e.g. 'greenhouse', 'lever', 'ashby').
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Human friendly name (e.g. 'Greenhouse', 'Lever', 'Ashby HQ').
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Brief summary of what this provider queries.
        """
        pass

    @abstractmethod
    async def search(self, query: JobSearchQuery) -> List[NormalizedJob]:
        """
        Search jobs matching the query parameters and return a list of normalized jobs.

        Args:
            query: `JobSearchQuery` containing keyword, location, etc.

        Returns:
            List of `NormalizedJob` instances.
        """
        pass

    @abstractmethod
    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        """
        Fetch full details for a single job URL.

        Args:
            url: The job listing URL.

        Returns:
            `NormalizedJob` or None if not found/error.
        """
        pass
