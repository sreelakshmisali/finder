"""
Crawl Package

Multi-stage job discovery crawling components:
- URLNormalizer / URLDeduplicator
- JobLinkExtractor (generic HTML listing pages)
- ATSLinkExtractor (per-ATS platform dedicated extractors)
- CrawlScheduler (two-stage pipeline orchestrator)
"""
