"""
Scheduler Configuration

Defines tunables and provider priority configurations for the crawl scheduler.
"""

from dataclasses import dataclass, field
import json
import os
from typing import Dict, Any, Optional


@dataclass
class ProviderPriorityConfig:
    """Priority and budget limits for a single provider category."""
    priority: int          # Lower = higher priority (1 = highest)
    max_job_pages: int     # Max job posting URLs allocated from this provider
    max_listing_pages: int # Max listing/career pages crawled
    weight: float          # SWRR selection weight


@dataclass  
class SchedulerConfig:
    """All crawl scheduling parameters, fully configurable."""
    
    # Global budgets
    global_crawl_budget: int = 60            # Total job posting URLs to extract
    max_candidate_pages: int = 60            # Max candidate search engine URLs to process
    max_concurrent_fetches: int = 30         # Concurrency cap for Stage 4 extraction & candidate fetches
    fetch_timeout: float = 3.5
    
    # Global Company Cap (Single source of truth used by Scheduler AND Stage 6)
    max_jobs_per_company: int = 5
    
    # Default provider priority table
    provider_priorities: Dict[str, ProviderPriorityConfig] = field(default_factory=lambda: {
        "company_career":    ProviderPriorityConfig(priority=1, max_job_pages=25, max_listing_pages=5, weight=3.0),
        "infopark":          ProviderPriorityConfig(priority=2, max_job_pages=20, max_listing_pages=3, weight=2.5),
        "technopark":        ProviderPriorityConfig(priority=2, max_job_pages=20, max_listing_pages=3, weight=2.5),
        "greenhouse":        ProviderPriorityConfig(priority=3, max_job_pages=20, max_listing_pages=5, weight=2.0),
        "lever":             ProviderPriorityConfig(priority=3, max_job_pages=20, max_listing_pages=5, weight=2.0),
        "ashby":             ProviderPriorityConfig(priority=3, max_job_pages=20, max_listing_pages=5, weight=2.0),
        "workday":           ProviderPriorityConfig(priority=4, max_job_pages=15, max_listing_pages=3, weight=1.5),
        "smartrecruiters":   ProviderPriorityConfig(priority=4, max_job_pages=15, max_listing_pages=3, weight=1.5),
        "linkedin":          ProviderPriorityConfig(priority=5, max_job_pages=12, max_listing_pages=3, weight=1.0),
        "generic_board":     ProviderPriorityConfig(priority=6, max_job_pages=10, max_listing_pages=2, weight=0.8),
    })
    
    # LinkedIn mode ("external_only" | "easy_apply_only" | "all")
    linkedin_mode: str = "external_only"

    @classmethod
    def from_env(cls) -> "SchedulerConfig":
        """Loads configuration from env vars, supporting optional JSON provider overrides."""
        config = cls()
        config.global_crawl_budget = int(os.getenv("CRAWL_BUDGET", "60"))
        config.max_candidate_pages = int(os.getenv("MAX_CANDIDATE_PAGES", "60"))
        config.max_concurrent_fetches = int(os.getenv("MAX_CONCURRENT_FETCHES", "15"))
        config.max_jobs_per_company = int(os.getenv("MAX_JOBS_PER_COMPANY", "5"))
        config.linkedin_mode = os.getenv("LINKEDIN_MODE", "external_only")
        
        overrides_json = os.getenv("PROVIDER_OVERRIDES")
        if overrides_json:
            try:
                overrides = json.loads(overrides_json)
                for prov, data in overrides.items():
                    if prov in config.provider_priorities:
                        cur = config.provider_priorities[prov]
                        config.provider_priorities[prov] = ProviderPriorityConfig(
                            priority=data.get("priority", cur.priority),
                            max_job_pages=data.get("max_job_pages", cur.max_job_pages),
                            max_listing_pages=data.get("max_listing_pages", cur.max_listing_pages),
                            weight=data.get("weight", cur.weight),
                        )
            except Exception:
                pass
        return config
