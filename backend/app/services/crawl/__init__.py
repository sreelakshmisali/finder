"""
Crawl Package

Multi-stage job discovery crawling components:
- URLNormalizer / URLDeduplicator
- JobLinkExtractor (generic HTML listing pages)
- ATSLinkExtractor (per-ATS platform dedicated extractors)
- CrawlScheduler (two-stage pipeline orchestrator)
- ProviderClassifier (URL provider classification & company extraction)
- DiversityScheduler (Smooth Weighted Round Robin budget allocation)
- LinkedInHandler (Pure HTML parser for LinkedIn external apply links)
"""

from app.services.crawl.url_utils import URLNormalizer, URLDeduplicator
from app.services.crawl.job_link_extractor import JobLinkExtractor
from app.services.crawl.ats_link_extractor import get_ats_extractor
from app.services.crawl.crawl_scheduler import CrawlScheduler
from app.services.crawl.provider_classifier import ProviderClassifier
from app.services.crawl.diversity_scheduler import DiversityScheduler
from app.services.crawl.linkedin_handler import LinkedInHandler

__all__ = [
    "URLNormalizer",
    "URLDeduplicator",
    "JobLinkExtractor",
    "get_ats_extractor",
    "CrawlScheduler",
    "ProviderClassifier",
    "DiversityScheduler",
    "LinkedInHandler",
]
