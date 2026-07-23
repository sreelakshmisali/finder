"""
Unit & Integration Tests for Job Extractor Service (Task 15)

Tests PageFetcher, SkillAndApplyExtractor, JobExtractor service, JS SPA detection,
relative/absolute Apply URL resolution, and error tolerance.
"""

import asyncio
from typing import Optional
from app.services.extraction.page_fetcher import SmartPageFetcher, HttpFetcher, PlaywrightFetcher
from app.services.extraction.skill_apply_extractor import SkillAndApplyExtractor
from app.services.job_extractor import JobExtractor
from app.schemas.job import NormalizedJob
from app.providers.search_engine.base_search import SearchResult


class MockHttpFetcher(HttpFetcher):
    """
    Mock HttpFetcher providing synthetic static HTML documents.
    """
    def __init__(self, responses: dict):
        self.responses = responses

    async def fetch(self, url: str, timeout: float = 10.0) -> Optional[str]:
        return self.responses.get(url, "")


class MockPlaywrightFetcher(PlaywrightFetcher):
    """
    Mock PlaywrightFetcher simulating rendered HTML for JS Single Page Apps.
    """
    def __init__(self, responses: dict):
        self.responses = responses

    async def fetch(self, url: str, timeout: float = 15.0) -> Optional[str]:
        return self.responses.get(url, "")


def test_js_spa_detection():
    """
    Verify SmartPageFetcher correctly identifies JS SPA shells (e.g. empty <div id="root">).
    """
    static_shell = '<html><head><title>Loading...</title></head><body><div id="root"></div></body></html>'
    normal_html = '<html><head><title>Backend Engineer at Stripe</title></head><body><h1>Job Description</h1><p>We are hiring a Python Engineer with PostgreSQL experience.</p></body></html>'

    assert SmartPageFetcher._is_js_spa_shell(static_shell) is True
    assert SmartPageFetcher._is_js_spa_shell(normal_html) is False


def test_skill_and_apply_url_extraction():
    """
    Test extraction of technical skills and relative Apply URL resolution.
    """
    page_url = "https://techcorp.io/careers/python-developer"
    html = '''
    <html>
      <body>
        <h1>Python Developer</h1>
        <p>Requirements: Python, FastAPI, Docker, and PostgreSQL.</p>
        <div class="actions">
          <a href="/apply/job-99" class="btn-primary apply-button">Apply Now</a>
        </div>
      </body>
    </html>
    '''
    skills, apply_url = SkillAndApplyExtractor.extract_skills_and_apply_url(
        page_url=page_url,
        html=html,
        description="Python FastAPI Docker PostgreSQL"
    )

    assert "Python" in skills
    assert "FastAPI" in skills
    assert "Docker" in skills
    assert "PostgreSQL" in skills
    assert apply_url == "https://techcorp.io/apply/job-99"


def test_job_extractor_static_page():
    """
    Test converting a career page HTML into a NormalizedJob object.
    """
    target_url = "https://figma.com/careers/backend-lead"
    html = '''
    <html>
      <head>
        <title>Backend Lead Engineer</title>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org/",
          "@type": "JobPosting",
          "title": "Backend Lead Engineer",
          "hiringOrganization": {
            "@type": "Organization",
            "name": "Figma"
          },
          "jobLocation": {
            "@type": "Place",
            "address": {
              "addressLocality": "San Francisco"
            }
          },
          "description": "Lead core backend systems using Python, Go, and Redis."
        }
        </script>
      </head>
      <body>
        <h1>Backend Lead Engineer</h1>
        <div>Full-time Job</div>
        <h2>Requirements</h2>
        <a href="https://figma.com/apply/backend-lead" class="apply">Apply for this Job</a>
      </body>
    </html>
    '''
    mock_http = MockHttpFetcher({target_url: html})
    mock_pw = MockPlaywrightFetcher({})
    smart_fetcher = SmartPageFetcher(http_fetcher=mock_http, playwright_fetcher=mock_pw)

    extractor = JobExtractor(fetcher=smart_fetcher)
    job = asyncio.run(extractor.extract_from_url(target_url))

    assert job is not None
    assert isinstance(job, NormalizedJob)
    assert job.title == "Backend Lead Engineer"
    assert job.company == "Figma"
    assert job.location == "San Francisco"
    assert job.url == target_url
    assert job.apply_url == "https://figma.com/apply/backend-lead"
    assert "Python" in job.required_skills
    assert "Go" in job.required_skills or "Redis" in job.required_skills


def test_job_extractor_js_spa_fallback():
    """
    Test that JobExtractor uses Playwright fallback when static HTML is a JS SPA shell.
    """
    target_url = "https://spa-company.io/careers/123"
    static_shell = '<html><body><div id="root"></div></body></html>'
    rendered_html = '''
    <html>
      <head>
        <title>Senior React Engineer</title>
        <meta property="og:title" content="Senior React Engineer" />
        <meta property="og:site_name" content="SPA Corp" />
        <meta property="og:description" content="Build modern user interfaces with React, TypeScript, and Tailwind." />
      </head>
      <body>
        <h1>Senior React Engineer</h1>
        <div>Full-time, Salary</div>
        <h2>Responsibilities</h2>
        <a href="/careers/123/apply" class="apply">Submit Application</a>
      </body>
    </html>
    '''
    mock_http = MockHttpFetcher({target_url: static_shell})
    mock_pw = MockPlaywrightFetcher({target_url: rendered_html})
    smart_fetcher = SmartPageFetcher(http_fetcher=mock_http, playwright_fetcher=mock_pw)

    extractor = JobExtractor(fetcher=smart_fetcher)
    job = asyncio.run(extractor.extract_from_url(target_url))

    assert job is not None
    assert job.title == "Senior React Engineer"
    assert job.company == "SPA Corp"
    assert job.apply_url == "https://spa-company.io/careers/123/apply"
    assert "React" in job.required_skills or "Typescript" in job.required_skills


def test_job_extractor_error_tolerance():
    """
    Verify that unparseable or broken URLs return None without throwing exceptions.
    """
    broken_url = "https://nonexistent-domain-404.com/job"
    mock_http = MockHttpFetcher({broken_url: None})
    mock_pw = MockPlaywrightFetcher({broken_url: None})
    smart_fetcher = SmartPageFetcher(http_fetcher=mock_http, playwright_fetcher=mock_pw)

    extractor = JobExtractor(fetcher=smart_fetcher)
    job = asyncio.run(extractor.extract_from_url(broken_url))

    assert job is None


if __name__ == "__main__":
    test_js_spa_detection()
    test_skill_and_apply_url_extraction()
    test_job_extractor_static_page()
    test_job_extractor_js_spa_fallback()
    test_job_extractor_error_tolerance()
    print("ALL 5 JOB EXTRACTOR TESTS PASSED SUCCESSFULLY!")
