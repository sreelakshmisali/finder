"""
Unit tests for DiversityScheduler and Smooth Weighted Round Robin (SWRR) allocation.
"""

import pytest
from app.core.scheduler_config import SchedulerConfig, ProviderPriorityConfig
from app.schemas.tagged_url import TaggedURL
from app.services.crawl.diversity_scheduler import DiversityScheduler
from app.services.crawl.provider_classifier import ProviderClassifier
from app.services.crawl.linkedin_handler import LinkedInHandler


def test_swrr_exact_sequence():
    """
    Verifies that DiversityScheduler produces the exact mathematical SWRR sequence for weights 3:2:1.
    """
    config = SchedulerConfig(
        global_crawl_budget=6,
        max_jobs_per_company=10,
        provider_priorities={
            "provA": ProviderPriorityConfig(priority=1, max_job_pages=10, max_listing_pages=5, weight=3.0),
            "provB": ProviderPriorityConfig(priority=2, max_job_pages=10, max_listing_pages=5, weight=2.0),
            "provC": ProviderPriorityConfig(priority=3, max_job_pages=10, max_listing_pages=5, weight=1.0),
        }
    )
    scheduler = DiversityScheduler(config)
    
    # Input: 5 URLs per provider
    urls = [
        TaggedURL(url=f"http://{p}.com/{i}", provider=p, priority_score=100) 
        for p in ["provA", "provB", "provC"] for i in range(5)
    ]
            
    allocated = scheduler.allocate(urls)
    sequence = [u.provider for u in allocated]
    
    # Expected SWRR sequence for weights 3, 2, 1:
    # Tick 1: A(3), B(2), C(1) -> Max A -> Output A
    # Tick 2: A(0), B(4), C(2) -> Max B -> Output B
    # Tick 3: A(3), B(0), C(3) -> Max A -> Output A
    # Tick 4: A(0), B(2), C(4) -> Max C -> Output C
    # Tick 5: A(3), B(4), C(-1) -> Max B -> Output B
    # Tick 6: A(6), B(0), C(0) -> Max A -> Output A
    expected = ["provA", "provB", "provA", "provC", "provB", "provA"]
    assert sequence == expected


def test_swrr_global_company_cap():
    """
    Verifies that global company cap (e.g. 2) skips URLs for a company across all providers combined.
    """
    config = SchedulerConfig(
        global_crawl_budget=10,
        max_jobs_per_company=2,
        provider_priorities={
            "provA": ProviderPriorityConfig(priority=1, max_job_pages=10, max_listing_pages=5, weight=2.0),
            "provB": ProviderPriorityConfig(priority=2, max_job_pages=10, max_listing_pages=5, weight=2.0),
        }
    )
    scheduler = DiversityScheduler(config)

    urls = [
        # Company Acme has 2 in provA, 2 in provB
        TaggedURL(url="http://greenhouse.io/acme/1", provider="provA", company="Acme", priority_score=90),
        TaggedURL(url="http://greenhouse.io/acme/2", provider="provA", company="Acme", priority_score=80),
        TaggedURL(url="http://lever.co/acme/3", provider="provB", company="Acme", priority_score=95),
        TaggedURL(url="http://lever.co/acme/4", provider="provB", company="Acme", priority_score=85),
        # Company Beta has URLs
        TaggedURL(url="http://greenhouse.io/beta/1", provider="provA", company="Beta", priority_score=70),
        TaggedURL(url="http://lever.co/beta/2", provider="provB", company="Beta", priority_score=75),
    ]

    allocated = scheduler.allocate(urls)
    acme_jobs = [u for u in allocated if u.company == "Acme"]
    assert len(acme_jobs) == 2  # Exactly 2 allowed globally across provA and provB


def test_provider_classifier_fallback():
    """
    Verifies that ProviderClassifier tags known domains correctly and defaults unknown domains to generic_board,
    unless path contains career signals.
    """
    assert ProviderClassifier.classify("https://boards.greenhouse.io/stripe/jobs/123") == "greenhouse"
    assert ProviderClassifier.classify("https://jobs.lever.co/netflix/456") == "lever"
    assert ProviderClassifier.classify("https://spgi.wd5.myworkdayjobs.com/careers") == "workday"
    assert ProviderClassifier.classify("https://infopark.in/companies/jobs") == "infopark"
    
    # Path with career signals -> company_career
    assert ProviderClassifier.classify("https://acme.com/careers/openings") == "company_career"
    
    # Unknown domain with no career signals -> generic_board
    assert ProviderClassifier.classify("https://unknown-aggregator.com/post/999") == "generic_board"


def test_provider_classifier_company_extraction():
    """
    Verifies heuristic company extraction from ATS URLs.
    """
    assert ProviderClassifier.extract_company_name("https://boards.greenhouse.io/stripe/jobs/123") == "Stripe"
    assert ProviderClassifier.extract_company_name("https://jobs.lever.co/netflix/456") == "Netflix"
    assert ProviderClassifier.extract_company_name("https://ashbyhq.com/notion/789") == "Notion"


def test_linkedin_handler_pure_parser():
    """
    Verifies that LinkedInHandler parses raw_html with 0 HTTP calls.
    """
    raw_html_with_offsite = """
    <html>
      <body>
        <a data-tracking-control-name="public_jobs_apply-link-offsite_sign-up" href="https://boards.greenhouse.io/acme/jobs/101">
          Apply on Company Site
        </a>
      </body>
    </html>
    """
    ext_url, is_easy = LinkedInHandler.parse_linkedin_html(raw_html_with_offsite, "https://linkedin.com/jobs/view/123")
    assert ext_url == "https://boards.greenhouse.io/acme/jobs/101"
    assert is_easy is False

    raw_html_easy_apply = "<html><body><button>Easy Apply</button></body></html>"
    ext_url2, is_easy2 = LinkedInHandler.parse_linkedin_html(raw_html_easy_apply, "https://linkedin.com/jobs/view/124")
    assert ext_url2 is None
    assert is_easy2 is True
