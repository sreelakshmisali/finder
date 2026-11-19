"""
Unit & Integration Tests for Job Extractor Service (Task 15)

Tests PageFetcher, SkillAndApplyExtractor, JobExtractor service, JS SPA detection,
relative/absolute Apply URL resolution, and error tolerance.
"""

import asyncio
import re
from typing import Optional
import pytest
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


# ─── Greenhouse react-portal-mount-point SPA-shell detection ─────────────────

# Real-world shape: Greenhouse's public job-board template serves an
# individual job URL (boards.greenhouse.io/{company}/jobs/{id}) as the
# company's job INDEX page in static HTML (substantial boilerplate text),
# with the specific job's content client-side rendered into the portal
# mount point. This fixture mirrors that shape (~2000+ chars of real text).
_GREENHOUSE_SHELL_HTML = '''
<html>
  <head><title>Jobs at WIN Home Inspection</title></head>
  <body>
    <div id="react-portal-mount-point"></div>
    <main class="main font-secondary">
      <div class="index--content">
        <h1 class="page-header font-primary">Current openings at WIN Home Inspection</h1>
        <div class="index--description">
          <p>At WIN, we are transforming delivery of actionable insights for homeowners to help
          improve health, safety and quality of life while saving significantly in repair bills
          with preventive maintenance. We are doing so by building scalable models, investing in
          the cloud, data science, artificial intelligence, machine learning, and unmatched
          training and certification programs.</p>
          <p>Our home is central to our mental and physical health. Home is where we build
          memories, grow together with our loved ones, and find comfort, safety and security.
          Which is why at WIN, we continue to reimagine deep insights via inspection and testing
          services for millions of residential and commercial facilities to bring peace of mind
          via actionable insights.</p>
          <p>If you are interested in making a difference, explore our current openings below.</p>
        </div>
      </div>
    </main>
  </body>
</html>
'''


# A real Playwright render of a Greenhouse job page includes the full
# client-side-hydrated DOM (nav, footer, scripts, the original shell markup
# plus the injected job content) — realistically longer than the raw SSR
# shell. SmartPageFetcher.fetch() only accepts the Playwright result when it
# is longer than the static shell (pre-existing, unmodified behaviour), so
# this fixture is padded to reflect that real-world size relationship.
_GREENHOUSE_RENDERED_HTML = '''
<html>
  <head>
    <title>Backend Engineer - WIN Home Inspection</title>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org/",
      "@type": "JobPosting",
      "title": "Backend Engineer",
      "hiringOrganization": {"@type": "Organization", "name": "WIN Home Inspection"},
      "jobLocation": {"@type": "Place", "address": {"addressLocality": "Remote"}},
      "description": "Build scalable Python microservices for our inspection platform."
    }
    </script>
  </head>
  <body>
    <div id="react-portal-mount-point">
      <header class="site-header"><nav>Home | Careers | About</nav></header>
      <h1>Backend Engineer</h1>
      <div class="job-meta">Remote &middot; Full-time &middot; Engineering</div>
      <h2>About the role</h2>
      <p>WIN Home Inspection is looking for a Backend Engineer to join our growing
      engineering team. You will design and build scalable services that power our
      inspection platform used by thousands of homeowners and inspectors nationwide.</p>
      <h2>Requirements</h2>
      <p>Experience with Python, FastAPI, and PostgreSQL required. Familiarity with
      Docker, CI/CD pipelines, and cloud infrastructure (AWS) is a strong plus.</p>
      <h2>What you'll do</h2>
      <p>Collaborate with cross-functional teams, own services end-to-end, and
      participate in on-call rotations to keep our platform reliable.</p>
      <a href="https://boards.greenhouse.io/winhomeinspection/jobs/4252546006/apply" class="apply">Apply Now</a>
      <footer class="site-footer">&copy; WIN Home Inspection. All rights reserved.</footer>
    </div>
  </body>
</html>
'''


def test_greenhouse_react_portal_mount_point_detected_as_spa_shell():
    """
    (1) A Greenhouse individual job URL's static response — which contains
    the react-portal-mount-point marker plus substantial company boilerplate
    text (the board index page) — must be detected as a JS SPA shell, even
    though its text content far exceeds the generic ambiguous-mount 100-char
    threshold.
    """
    assert SmartPageFetcher._is_js_spa_shell(_GREENHOUSE_SHELL_HTML) is True
    # Sanity: confirm this fixture really does have substantial text, so the
    # detection isn't accidentally passing via the generic short-text path.
    text_only = re.sub(r"<[^>]+>", "", _GREENHOUSE_SHELL_HTML).strip()
    assert len(text_only) > 500, "Fixture must mimic real Greenhouse boilerplate length"


def test_generic_spa_mount_detection_still_works():
    """
    (2) Existing generic SPA-shell detections (id="root", id="app", etc. with
    minimal surrounding text) continue to work unchanged.
    """
    root_shell = '<html><body><div id="root"></div></body></html>'
    app_shell = '<html><body><div id="app"></div></body></html>'
    next_shell = '<html><body><div id="__next"></div></body></html>'
    loading_shell = '<html><body><div class="loading"></div></body></html>'

    assert SmartPageFetcher._is_js_spa_shell(root_shell) is True
    assert SmartPageFetcher._is_js_spa_shell(app_shell) is True
    assert SmartPageFetcher._is_js_spa_shell(next_shell) is True
    assert SmartPageFetcher._is_js_spa_shell(loading_shell) is True


def test_generic_spa_mount_with_substantial_content_not_flagged():
    """
    A page using a generic mount id (#root/#app) that ALSO ships full,
    substantial content (i.e. actually server-rendered) must NOT be flagged
    as a shell — the ambiguous-mount text-length guard must still apply to
    these ids (only the Greenhouse marker bypasses it).
    """
    real_content_with_root_div = (
        '<html><body><div id="root">'
        + ("Backend Engineer position full description with lots of real content. " * 20)
        + '</div></body></html>'
    )
    assert SmartPageFetcher._is_js_spa_shell(real_content_with_root_div) is False


def test_normal_pages_not_misclassified_as_spa_shell():
    """
    (3) Normal, fully server-rendered non-SPA pages (no mount markers, no
    react-portal-mount-point, plenty of real text) must not be incorrectly
    classified as SPA shells.
    """
    normal_html = (
        '<html><head><title>Backend Engineer at Stripe</title></head>'
        '<body><h1>Job Description</h1>'
        '<p>We are hiring a Python Engineer with PostgreSQL experience. '
        'Responsibilities include building scalable backend services, '
        'collaborating with cross-functional teams, and maintaining '
        'high-quality production code.</p></body></html>'
    )
    assert SmartPageFetcher._is_js_spa_shell(normal_html) is False


@pytest.mark.asyncio
async def test_greenhouse_shell_triggers_playwright_rendering():
    """
    (4) When SmartPageFetcher.fetch() receives the Greenhouse shell HTML from
    the static HttpFetcher, it must invoke the Playwright fallback and return
    the rendered content instead of the shell.
    """
    url = "https://boards.greenhouse.io/winhomeinspection/jobs/4252546006"
    mock_http = MockHttpFetcher({url: _GREENHOUSE_SHELL_HTML})
    mock_pw = MockPlaywrightFetcher({url: _GREENHOUSE_RENDERED_HTML})
    smart_fetcher = SmartPageFetcher(http_fetcher=mock_http, playwright_fetcher=mock_pw)

    result_html = await smart_fetcher.fetch(url)

    assert result_html == _GREENHOUSE_RENDERED_HTML
    # The rendered DOM still contains the mount div (React fills it in-place),
    # but now it also contains the actual job content injected by the client —
    # content that only exists in the rendered version, not the raw shell.
    assert "Backend Engineer" in result_html
    assert "Requirements" in result_html
    assert "About the role" in result_html


@pytest.mark.asyncio
async def test_greenhouse_shell_reaches_extractor_as_real_job():
    """
    (5) End-to-end: after Playwright rendering, the actual Greenhouse job
    content reaches the existing JobExtractor/classification pipeline and
    produces a valid NormalizedJob — proving the classifier now receives the
    correct rendered page rather than being weakened to accept the shell.
    """
    url = "https://boards.greenhouse.io/winhomeinspection/jobs/4252546006"
    mock_http = MockHttpFetcher({url: _GREENHOUSE_SHELL_HTML})
    mock_pw = MockPlaywrightFetcher({url: _GREENHOUSE_RENDERED_HTML})
    smart_fetcher = SmartPageFetcher(http_fetcher=mock_http, playwright_fetcher=mock_pw)

    extractor = JobExtractor(fetcher=smart_fetcher)
    job = await extractor.extract_from_url(url)

    assert job is not None, (
        "Job must be successfully extracted after Playwright renders the "
        "real Greenhouse job content (classifier unchanged, receives correct HTML)"
    )
    assert job.title == "Backend Engineer"
    assert job.company == "WIN Home Inspection"
    assert job.source == "greenhouse"
    assert "Python" in job.required_skills


@pytest.mark.asyncio
async def test_greenhouse_shell_without_playwright_rescue_is_rejected():
    """
    Control case: if Playwright rendering is unavailable/fails, the raw shell
    HTML alone is correctly rejected by the classifier (COMPANY_PAGE) — this
    proves the classifier itself was not weakened; only the fetch layer was
    fixed to feed it the right content when rendering succeeds.
    """
    url = "https://boards.greenhouse.io/winhomeinspection/jobs/4252546006"
    mock_http = MockHttpFetcher({url: _GREENHOUSE_SHELL_HTML})
    mock_pw = MockPlaywrightFetcher({})  # Playwright fetch fails / returns nothing
    smart_fetcher = SmartPageFetcher(http_fetcher=mock_http, playwright_fetcher=mock_pw)

    extractor = JobExtractor(fetcher=smart_fetcher)
    job = await extractor.extract_from_url(url)

    # Playwright returned nothing, so SmartPageFetcher falls back to the shell
    # HTML, and the classifier correctly rejects it (same as before the fix).
    assert job is None


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

def test_job_extractor_attribution():
    """
    Test that JobExtractor correctly sets source attribution for ATS boards vs non-ATS sites.
    """
    mock_http = MockHttpFetcher({
        "https://jobs.lever.co/test/123": "<html><head><title>Lever Job</title><script type='application/ld+json'>{\"@type\":\"JobPosting\",\"title\":\"Lever Job\"}</script></head><body>Lever Job<a href='/apply'>Apply</a></body></html>",
        "https://boards.greenhouse.io/test/123": "<html><head><title>Greenhouse Job</title><script type='application/ld+json'>{\"@type\":\"JobPosting\",\"title\":\"Greenhouse Job\"}</script></head><body>Greenhouse Job<a href='/apply'>Apply</a></body></html>",
        "https://jobs.ashbyhq.com/test/123": "<html><head><title>Ashby Job</title><script type='application/ld+json'>{\"@type\":\"JobPosting\",\"title\":\"Ashby Job\"}</script></head><body>Ashby Job<a href='/apply'>Apply</a></body></html>",
        "https://somecompany.com/careers/job": "<html><head><title>General Job</title><script type='application/ld+json'>{\"@type\":\"JobPosting\",\"title\":\"General Job\"}</script></head><body>General Job<a href='https://somecompany.com/apply'>Apply</a></body></html>",
    })
    mock_pw = MockPlaywrightFetcher({})
    smart_fetcher = SmartPageFetcher(http_fetcher=mock_http, playwright_fetcher=mock_pw)
    extractor = JobExtractor(fetcher=smart_fetcher)

    # Test Lever
    job = asyncio.run(extractor.extract_from_url("https://jobs.lever.co/test/123", skip_classification=True))
    assert job is not None
    assert job.source == "lever"
    
    # Test Greenhouse
    job = asyncio.run(extractor.extract_from_url("https://boards.greenhouse.io/test/123", skip_classification=True))
    assert job is not None
    assert job.source == "greenhouse"

    # Test Ashby
    job = asyncio.run(extractor.extract_from_url("https://jobs.ashbyhq.com/test/123", skip_classification=True))
    assert job is not None
    assert job.source == "ashby"

    # Test Non-ATS
    job = asyncio.run(extractor.extract_from_url("https://somecompany.com/careers/job", skip_classification=True))
    assert job is not None
    assert job.source == "search_engine"


if __name__ == "__main__":
    test_js_spa_detection()
    test_skill_and_apply_url_extraction()
    test_job_extractor_static_page()
    test_job_extractor_js_spa_fallback()
    test_job_extractor_error_tolerance()

