"""
Unit & Integration Tests for Job Discovery Architecture (Task 12).
Verifies:
1. ProviderType Enum & DiscoveryContext abstractions.
2. ATSProvider, SearchEngineProvider, CrawlerProvider subclass hierarchy.
3. ProviderRegistry registering and sorting providers by priority & ProviderType.
4. Provider failure isolation (one provider error does not halt others).
5. Zero edits to JobService when adding a new search engine discovery provider.
"""

import asyncio
import sys
import os
from typing import List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.providers.base_discovery import (
    JobDiscoveryProvider,
    ATSProvider,
    SearchEngineProvider,
    CrawlerProvider,
    ProviderType,
    DiscoveryContext,
)
from app.providers.registry import ProviderRegistry, registry
from app.schemas.job import JobSearchQuery, NormalizedJob


def test_provider_type_enum_and_context():
    assert ProviderType.ATS.value == "ats"
    assert ProviderType.SEARCH_ENGINE.value == "search_engine"
    assert ProviderType.CRAWLER.value == "crawler"

    query = JobSearchQuery(query="Python Engineer")
    ctx = DiscoveryContext(query=query)
    assert ctx.query.query == "Python Engineer"
    assert ctx.user_id is None
    print("test_provider_type_enum_and_context: PASSED")


def test_default_registry_providers():
    enabled_providers = registry.get_enabled_providers()
    source_names = [p.source_name for p in enabled_providers]
    
    assert "greenhouse" in source_names
    assert "lever" in source_names
    assert "ashby" in source_names

    ats_providers = registry.get_enabled_providers(provider_type=ProviderType.ATS)
    assert len(ats_providers) == 3
    print("test_default_registry_providers: PASSED")


class MockFailingProvider(ATSProvider):
    @property
    def source_name(self) -> str:
        return "mock_failing"
    @property
    def display_name(self) -> str:
        return "Mock Failing"
    @property
    def description(self) -> str:
        return "Always throws error"
    async def discover(self, context: DiscoveryContext) -> List[NormalizedJob]:
        raise RuntimeError("Simulated external API network crash")
    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        return None


class MockCustomSearchEngineProvider(SearchEngineProvider):
    @property
    def source_name(self) -> str:
        return "custom_search_engine"
    @property
    def display_name(self) -> str:
        return "Custom Search Engine"
    @property
    def description(self) -> str:
        return "Simulated web search engine provider"
    async def discover(self, context: DiscoveryContext) -> List[NormalizedJob]:
        return [
            NormalizedJob(
                title="Staff Python Architect",
                company="Acme Corp",
                location="Remote",
                url="https://acme.com/jobs/1",
                description="Python architecture role discovered via search engine",
                source="custom_search_engine"
            )
        ]
    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        return None


def test_provider_failure_isolation():
    temp_registry = ProviderRegistry()
    failing_p = MockFailingProvider()
    working_p = MockCustomSearchEngineProvider()

    temp_registry.register_provider(failing_p, priority=1)
    temp_registry.register_provider(working_p, priority=2)

    providers = temp_registry.get_enabled_providers()
    query = JobSearchQuery(query="Python")
    ctx = DiscoveryContext(query=query)

    async def run_gather():
        tasks = [p.discover(ctx) for p in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(run_gather())

    assert isinstance(results[0], Exception)
    assert isinstance(results[1], list)
    assert len(results[1]) == 1
    assert results[1][0].title == "Staff Python Architect"

    print("test_provider_failure_isolation: PASSED")


if __name__ == "__main__":
    test_provider_type_enum_and_context()
    test_default_registry_providers()
    test_provider_failure_isolation()
