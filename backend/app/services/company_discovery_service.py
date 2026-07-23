"""
Company Career Discovery Service

Service responsible ONLY for discovering companies and their career portals matching
technology, location, or industry criteria. Decoupled from job extraction and specific search engines.
"""

import asyncio
import logging
from typing import List, Optional, Set, Dict, Any
from urllib.parse import urlparse

from app.schemas.company import DiscoveredCompany, CompanySearchQuery
from app.providers.search_engine.base_search import SearchProvider, SearchResult
from app.providers.search_engine.google_search import GoogleSearchProvider
from app.providers.search_engine.bing_search import BingSearchProvider
from app.services.company_extraction.industry_classifier import RuleBasedIndustryClassifier, BaseIndustryClassifier
from app.services.company_extraction.tech_tag_extractor import TechTagExtractor

logger = logging.getLogger(__name__)


class CompanyDiscoveryService:
    """
    Service for company career portal discovery.
    """

    def __init__(
        self,
        search_providers: Optional[List[SearchProvider]] = None,
        classifier: Optional[BaseIndustryClassifier] = None
    ):
        self.search_providers = search_providers if search_providers is not None else [
            GoogleSearchProvider(),
            BingSearchProvider()
        ]
        self.classifier = classifier or RuleBasedIndustryClassifier()

    async def discover_companies(
        self,
        query: str,
        location: Optional[str] = None,
        technology: Optional[str] = None,
        limit: int = 10
    ) -> List[DiscoveredCompany]:
        """
        Discovers companies matching target query parameters.

        Args:
            query: Target search query string (e.g. 'Python startups India', 'AI companies careers').
            location: Optional geographic location filter.
            technology: Optional technology stack filter.
            limit: Maximum number of companies to return.

        Returns:
            List of `DiscoveredCompany` objects.
        """
        search_intent = self._build_search_intent(query=query, location=location, technology=technology)

        active_providers = [p for p in self.search_providers if p.is_available]
        if not active_providers:
            logger.info("No active search providers configured for company discovery. Using fallback discovery.")
            return self._generate_fallback_companies(query=query, limit=limit)

        # Concurrently query search providers
        tasks = [p.search(query=search_intent, limit=limit * 2) for p in active_providers]
        nested_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_results: List[SearchResult] = []
        for res in nested_results:
            if isinstance(res, list):
                all_results.extend(res)

        if not all_results:
            return self._generate_fallback_companies(query=query, limit=limit)

        return self._process_search_results(all_results=all_results, raw_query=query, limit=limit)

    def _build_search_intent(
        self,
        query: str,
        location: Optional[str],
        technology: Optional[str]
    ) -> str:
        parts = [query.strip()]
        if technology and technology.lower() not in query.lower():
            parts.append(technology.strip())
        if location and location.lower() not in query.lower():
            parts.append(location.strip())

        combined = " ".join(parts)
        if "careers" not in combined.lower() and "jobs" not in combined.lower():
            combined += " careers"

        return combined

    def _process_search_results(
        self,
        all_results: List[SearchResult],
        raw_query: str,
        limit: int
    ) -> List[DiscoveredCompany]:
        companies: List[DiscoveredCompany] = []
        seen_domains: Set[str] = set()

        for item in all_results:
            parsed = urlparse(item.url)
            domain = parsed.netloc.replace("www.", "").lower()

            if not domain or domain in seen_domains:
                continue

            # Skip general search engine domains
            if any(black in domain for black in ["google.", "bing.", "wikipedia.org", "linkedin.com/in"]):
                continue

            seen_domains.add(domain)

            # Derive company name from domain or title
            name = self._derive_company_name(item.title, domain)
            career_url = item.url
            website = f"{parsed.scheme}://{parsed.netloc}"

            # Classify Industry & Extract Tech Tags
            combined_text = f"{item.title} {item.snippet} {raw_query}"
            industry = self.classifier.classify(combined_text)
            tech_tags = TechTagExtractor.extract_tags(combined_text)

            companies.append(
                DiscoveredCompany(
                    name=name,
                    career_url=career_url,
                    industry=industry,
                    technology_tags=tech_tags,
                    website=website,
                    confidence_score=0.92,
                    discovery_source=item.engine
                )
            )

            if len(companies) >= limit:
                break

        return companies

    @staticmethod
    def _derive_company_name(title: str, domain: str) -> str:
        if " - " in title:
            candidate = title.split(" - ")[0].strip()
            if len(candidate) < 30 and candidate.lower() not in ["careers", "jobs"]:
                return candidate.title()
        if " | " in title:
            candidate = title.split(" | ")[0].strip()
            if len(candidate) < 30 and candidate.lower() not in ["careers", "jobs"]:
                return candidate.title()

        raw = domain.split(".")[0]
        return raw.capitalize()

    @staticmethod
    def _generate_fallback_companies(query: str, limit: int) -> List[DiscoveredCompany]:
        """
        Provides rich fallback company records for testing when external search API keys are unconfigured.
        """
        clean_q = query.lower()
        samples = [
            DiscoveredCompany(
                name="Hasura",
                career_url="https://hasura.io/careers",
                industry="Developer Tools & Cloud",
                technology_tags=["Python", "GraphQL", "PostgreSQL", "Docker"],
                website="https://hasura.io",
                confidence_score=0.95,
                discovery_source="fallback"
            ),
            DiscoveredCompany(
                name="Postman",
                career_url="https://www.postman.com/careers",
                industry="Developer Tools & Cloud",
                technology_tags=["Python", "Node.js", "AWS", "Docker"],
                website="https://www.postman.com",
                confidence_score=0.92,
                discovery_source="fallback"
            ),
            DiscoveredCompany(
                name="Razorpay",
                career_url="https://razorpay.com/jobs",
                industry="Fintech & Payments",
                technology_tags=["Python", "Go", "PostgreSQL", "Microservices"],
                website="https://razorpay.com",
                confidence_score=0.90,
                discovery_source="fallback"
            )
        ]

        if "ai" in clean_q:
            samples.insert(0, DiscoveredCompany(
                name="Sarvam AI",
                career_url="https://sarvam.ai/careers",
                industry="AI & Machine Learning",
                technology_tags=["Python", "PyTorch", "LLM", "FastAPI"],
                website="https://sarvam.ai",
                confidence_score=0.96,
                discovery_source="fallback"
            ))

        return samples[:limit]
