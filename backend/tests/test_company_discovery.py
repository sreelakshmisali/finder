"""
Unit & Integration Tests for Company Career Discovery Engine (Task 16)

Tests CompanyDiscoveryService, IndustryClassifier, TechTagExtractor,
duplicate company deduplication, and search provider integration.
"""

import asyncio
from app.schemas.company import DiscoveredCompany
from app.services.company_extraction.industry_classifier import RuleBasedIndustryClassifier
from app.services.company_extraction.tech_tag_extractor import TechTagExtractor
from app.services.company_discovery_service import CompanyDiscoveryService
from app.providers.search_engine.base_search import SearchProvider, SearchResult


class MockSearchEngineForCompany(SearchProvider):
    """
    Mock Search Engine returning company search results.
    """
    def __init__(self, results: list):
        self._results = results

    @property
    def name(self) -> str:
        return "mock_company_search"

    @property
    def display_name(self) -> str:
        return "Mock Company Search Engine"

    @property
    def is_available(self) -> bool:
        return True

    async def search(self, query: str, limit: int = 10) -> list:
        return self._results[:limit]


def test_industry_classifier():
    """
    Test rule-based classification of company industries.
    """
    classifier = RuleBasedIndustryClassifier()

    assert classifier.classify("Payment processing API gateway for online banking") == "Fintech & Payments"
    assert classifier.classify("Generative AI models and LLM infrastructure") == "AI & Machine Learning"
    assert classifier.classify("Cloud database and GraphQL developer tooling") == "Developer Tools & Cloud"
    assert classifier.classify("Random generic text") == "Technology"


def test_tech_tag_extractor():
    """
    Test extraction of technology tags from company text.
    """
    text = "We build high performance backend systems using Python, Django, FastAPI, Docker, and PostgreSQL on AWS."
    tags = TechTagExtractor.extract_tags(text)

    assert "Python" in tags
    assert "Django" in tags
    assert "FastAPI" in tags
    assert "PostgreSQL" in tags
    assert "Docker" in tags
    assert "AWS" in tags


def test_company_discovery_deduplication_and_extraction():
    """
    Test that CompanyDiscoveryService deduplicates duplicate domains and extracts company metadata.
    """
    mock_results = [
        SearchResult(title="Hasura - GraphQL Engine & Cloud Jobs", url="https://hasura.io/careers", snippet="Python Hasura GraphQL PostgreSQL", engine="g1"),
        SearchResult(title="Hasura Careers Duplicate", url="https://hasura.io/jobs/1", snippet="Python Hasura GraphQL", engine="g1"),
        SearchResult(title="Stripe - Global Payment Platform", url="https://stripe.com/jobs", snippet="Ruby Python Fintech Payments", engine="g1")
    ]
    mock_provider = MockSearchEngineForCompany(mock_results)

    service = CompanyDiscoveryService(search_providers=[mock_provider])
    companies = asyncio.run(service.discover_companies(query="Python startups India"))

    assert len(companies) == 2  # Hasura deduplicated from 2 results to 1
    assert any(c.name == "Hasura" for c in companies)
    assert any(c.name == "Stripe" for c in companies)

    hasura = next(c for c in companies if c.name == "Hasura")
    assert hasura.career_url == "https://hasura.io/careers"
    assert "Python" in hasura.technology_tags


def test_company_discovery_support_queries():
    """
    Test required support queries:
    - startups hiring Python engineers
    - AI companies careers
    - fintech backend jobs
    """
    service = CompanyDiscoveryService(search_providers=[])

    queries = [
        "startups hiring Python engineers",
        "AI companies careers",
        "fintech backend jobs"
    ]

    for q in queries:
        companies = asyncio.run(service.discover_companies(query=q, limit=5))
        assert len(companies) > 0
        assert isinstance(companies[0], DiscoveredCompany)
        assert bool(companies[0].name)
        assert bool(companies[0].career_url)


if __name__ == "__main__":
    test_industry_classifier()
    test_tech_tag_extractor()
    test_company_discovery_deduplication_and_extraction()
    test_company_discovery_support_queries()
    print("ALL 4 COMPANY DISCOVERY TESTS PASSED SUCCESSFULLY!")
