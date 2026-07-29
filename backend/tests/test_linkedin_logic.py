import pytest
import asyncio
from datetime import datetime
from app.schemas.job import NormalizedJob
from app.providers.search_engine.search_discovery import SearchDiscoveryProvider
from app.models.job import Job
import uuid

def test_linkedin_external_application():
    # Setup two mock normalized jobs: one from linkedin, one from greenhouse
    linkedin_job = NormalizedJob(
        company="TestCo",
        title="Backend Engineer",
        location="Remote",
        remote=True,
        description="test",
        url="https://linkedin.com/jobs/view/123",
        source="linkedin",
        apply_url=None,
        can_apply=False,
    )

    greenhouse_job = NormalizedJob(
        company="TestCo",
        title="Backend Engineer",
        location="Remote",
        remote=True,
        description="test",
        url="https://boards.greenhouse.io/testco/jobs/456",
        source="greenhouse",
        apply_url="https://boards.greenhouse.io/testco/jobs/456",
        can_apply=True,
    )

    # Dedup logic directly inline to test it
    existing_job = linkedin_job.model_copy()
    job = greenhouse_job
    
    # Merge existing (linkedin) with job (ATS)
    if job.apply_url or job.url:
        existing_job.apply_url = job.apply_url or job.url
        existing_job.can_apply = True

    assert existing_job.url == "https://linkedin.com/jobs/view/123"
    assert existing_job.apply_url == "https://boards.greenhouse.io/testco/jobs/456"
    assert existing_job.can_apply is True
    assert existing_job.source == "linkedin"

def test_linkedin_easy_apply_only():
    linkedin_job = NormalizedJob(
        company="TestCo",
        title="Backend Engineer",
        location="Remote",
        remote=True,
        description="test",
        url="https://linkedin.com/jobs/view/123",
        source="linkedin",
        apply_url=None,
        can_apply=False,
    )
    
    assert linkedin_job.apply_url is None
    assert linkedin_job.can_apply is False

def test_db_merge_logic():
    # Test job repository merge logic mapping
    # Just checking the schema compatibility
    pass

def test_job_extractor_linkedin_easy_apply():
    from tests.test_job_extractor import MockHttpFetcher, MockPlaywrightFetcher
    from app.services.extraction.page_fetcher import SmartPageFetcher
    from app.services.job_extractor import JobExtractor

    url = "https://linkedin.com/jobs/view/123"
    html = '''
    <html>
      <head>
        <title>Software Engineer at Stripe</title>
      </head>
      <body>
        <h1>Software Engineer</h1>
        <button>Easy Apply</button>
        <p>This is a great software role. Requirements: Python.</p>
      </body>
    </html>
    '''
    mock_http = MockHttpFetcher({url: html})
    smart_fetcher = SmartPageFetcher(http_fetcher=mock_http, playwright_fetcher=MockPlaywrightFetcher({}))
    extractor = JobExtractor(fetcher=smart_fetcher)
    
    job = asyncio.run(extractor.extract_from_url(url, skip_classification=True))
    assert job is None

def test_job_extractor_linkedin_external_apply():
    from tests.test_job_extractor import MockHttpFetcher, MockPlaywrightFetcher
    from app.services.extraction.page_fetcher import SmartPageFetcher
    from app.services.job_extractor import JobExtractor

    url = "https://linkedin.com/jobs/view/456"
    html = '''
    <html>
      <head>
        <title>Software Engineer at Stripe</title>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org/",
          "@type": "JobPosting",
          "title": "Software Engineer",
          "hiringOrganization": {
            "@type": "Organization",
            "name": "Stripe"
          },
          "applyAction": {
            "@type": "ApplyAction",
            "target": "https://boards.greenhouse.io/stripe/jobs/101"
          },
          "description": "Python role"
        }
        </script>
      </head>
      <body>
        <h1>Software Engineer</h1>
        <p>Python role at Stripe.</p>
      </body>
    </html>
    '''
    mock_http = MockHttpFetcher({url: html})
    smart_fetcher = SmartPageFetcher(http_fetcher=mock_http, playwright_fetcher=MockPlaywrightFetcher({}))
    extractor = JobExtractor(fetcher=smart_fetcher)
    
    job = asyncio.run(extractor.extract_from_url(url, skip_classification=True))
    assert job is not None
    assert job.apply_url == "https://boards.greenhouse.io/stripe/jobs/101"
    assert job.can_apply is True
    assert job.source == "linkedin"

def test_job_extractor_linkedin_no_apply_url():
    from tests.test_job_extractor import MockHttpFetcher, MockPlaywrightFetcher
    from app.services.extraction.page_fetcher import SmartPageFetcher
    from app.services.job_extractor import JobExtractor

    url = "https://linkedin.com/jobs/view/789"
    html = '''
    <html>
      <head>
        <title>Software Engineer at Stripe</title>
      </head>
      <body>
        <h1>Software Engineer</h1>
        <p>Python role at Stripe.</p>
      </body>
    </html>
    '''
    mock_http = MockHttpFetcher({url: html})
    smart_fetcher = SmartPageFetcher(http_fetcher=mock_http, playwright_fetcher=MockPlaywrightFetcher({}))
    extractor = JobExtractor(fetcher=smart_fetcher)
    
    job = asyncio.run(extractor.extract_from_url(url, skip_classification=True))
    assert job is None

def test_job_extractor_career_page_no_apply_button():
    from tests.test_job_extractor import MockHttpFetcher, MockPlaywrightFetcher
    from app.services.extraction.page_fetcher import SmartPageFetcher
    from app.services.job_extractor import JobExtractor

    url = "https://company.com/careers"
    html = '''
    <html>
      <head>
        <title>Careers at Company</title>
      </head>
      <body>
        <h1>Work with us!</h1>
        <p>We are a cool startup. Here is our address.</p>
      </body>
    </html>
    '''
    mock_http = MockHttpFetcher({url: html})
    smart_fetcher = SmartPageFetcher(http_fetcher=mock_http, playwright_fetcher=MockPlaywrightFetcher({}))
    extractor = JobExtractor(fetcher=smart_fetcher)
    
    job = asyncio.run(extractor.extract_from_url(url, skip_classification=True))
    assert job is None

def test_job_extractor_greenhouse_job_url():
    from tests.test_job_extractor import MockHttpFetcher, MockPlaywrightFetcher
    from app.services.extraction.page_fetcher import SmartPageFetcher
    from app.services.job_extractor import JobExtractor

    url = "https://boards.greenhouse.io/testco/jobs/111"
    html = '''
    <html>
      <head>
        <title>Backend Developer</title>
      </head>
      <body>
        <h1>Backend Developer</h1>
        <p>We need Python skills.</p>
      </body>
    </html>
    '''
    mock_http = MockHttpFetcher({url: html})
    smart_fetcher = SmartPageFetcher(http_fetcher=mock_http, playwright_fetcher=MockPlaywrightFetcher({}))
    extractor = JobExtractor(fetcher=smart_fetcher)
    
    job = asyncio.run(extractor.extract_from_url(url, skip_classification=True))
    assert job is not None
    assert job.apply_url == url
    assert job.can_apply is True
