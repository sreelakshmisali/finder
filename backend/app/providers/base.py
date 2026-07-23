"""
Legacy Job Provider Adapter

Re-exports `JobDiscoveryProvider`, `ATSProvider`, `ProviderType`, and `DiscoveryContext` from `base_discovery.py`.
Provides backward-compatible `JobProvider` base class.
"""

from typing import List, Optional
from app.providers.base_discovery import (
    JobDiscoveryProvider,
    ATSProvider,
    SearchEngineProvider,
    CrawlerProvider,
    ProviderType,
    DiscoveryContext,
)
from app.schemas.job import JobSearchQuery, NormalizedJob


class JobProvider(ATSProvider):
    """
    Backward-compatible JobProvider adapter.
    Inherits from ATSProvider and maps `search(query)` to `discover(context)`.
    """

    async def search(self, query: JobSearchQuery) -> List[NormalizedJob]:
        """
        Legacy search method delegating to discover().
        """
        context = DiscoveryContext(query=query)
        return await self.discover(context)


__all__ = [
    "JobDiscoveryProvider",
    "ATSProvider",
    "SearchEngineProvider",
    "CrawlerProvider",
    "ProviderType",
    "DiscoveryContext",
    "JobProvider",
]
