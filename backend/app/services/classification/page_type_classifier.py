"""
Page Type Classifier

Routing-focused classifier that determines what kind of web page a URL/HTML represents,
so the CrawlScheduler can route it to the correct handler:

  JOB_POSTING          → JobExtractor (direct extraction)
  ATS_CAREER_PAGE      → ATSLinkExtractor (drill down to individual jobs)
  JOB_LISTING_PAGE     → JobLinkExtractor (generic drill-down)
  COMPANY_CAREERS_HOME → JobLinkExtractor (generic drill-down)
  JOB_BOARD            → JobLinkExtractor (shallow pass only)
  BLOG/DOCS/HOME/etc.  → Discard

This is SEPARATE from the existing RuleBasedJobPageClassifier (which acts as the
gatekeeper for JobExtractor after a page has already been identified as a posting).
This classifier handles the earlier routing decision.
"""

import re
import json
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.schemas.classification import PageType, ClassificationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# URL-based ATS platform patterns → (PageType, sub_type)
# ---------------------------------------------------------------------------

_ATS_URL_PATTERNS: list[Tuple[re.Pattern, str]] = [
    (re.compile(r"boards(\.[a-z]+)?\.greenhouse\.io",    re.I), "greenhouse"),
    (re.compile(r"jobs\.lever\.co",                      re.I), "lever"),
    (re.compile(r"jobs\.ashbyhq\.com",                   re.I), "ashby"),
    (re.compile(r"\.myworkdayjobs\.com",                 re.I), "workday"),
    (re.compile(r"jobs\.smartrecruiters\.com",           re.I), "smartrecruiters"),
    (re.compile(r"jobs\.jobvite\.com",                   re.I), "jobvite"),
    (re.compile(r"\.bamboohr\.com",                      re.I), "bamboohr"),
    (re.compile(r"apply\.workable\.com",                 re.I), "workable"),
    (re.compile(r"jobs\.gusto\.com",                     re.I), "gusto"),
    (re.compile(r"careers\.icims\.com",                  re.I), "icims"),
    (re.compile(r"oracle\.taleo\.net",                   re.I), "taleo"),
]

# URL patterns for known job boards
_JOB_BOARD_DOMAINS = {
    "linkedin.com", "indeed.com", "glassdoor.com", "monster.com",
    "naukri.com", "simplyhired.com", "ziprecruiter.com", "dice.com",
    "wellfound.com", "ycombinator.com", "remoteok.com", "weworkremotely.com",
    "reactjobs.io", "nodeweekly.com", "builtin.com", "angel.co",
    "upwork.com", "jsgurujobs.com", "infopark.in",
}


# URL path segments that indicate a listing/search page (not an individual posting)
_LISTING_PATH_SIGNALS = [
    "/jobs", "/careers", "/openings", "/positions", "/vacancies",
    "/job-search", "/find-jobs", "/browse-jobs",
]

# URL path segments that strongly suggest an individual job page
_POSTING_PATH_PATTERNS = [
    re.compile(r"/jobs?/[\w\-%]{4,}",         re.I),
    re.compile(r"/careers?/[\w\-%]{8,}",      re.I),
    re.compile(r"/openings?/[\w\-%]{4,}",     re.I),
    re.compile(r"/positions?/[\w\-%]{4,}",    re.I),
    re.compile(r"/role/[\w\-%]{4,}",          re.I),
    re.compile(r"/\d{5,}",                    re.I),   # numeric IDs
]

# Page title / H1 keywords → discard
_DISCARD_TITLE_KEYWORDS = [
    "blog", "news", "press release", "documentation", "docs", "tutorial",
    "privacy policy", "terms of service", "cookie", "404", "not found",
    "login", "sign in", "register", "about us", "contact us",
]

# Page title signals that suggest a listing rather than a posting
_LISTING_TITLE_KEYWORDS = [
    "jobs at", "careers at", "open positions", "open roles",
    "job openings", "browse jobs", "search jobs", "find jobs",
    "all jobs", "current openings", "work with us",
]


class PageTypeClassifier:
    """
    Lightweight rule-based page type classifier for routing within the crawl pipeline.

    Classification precedence (first match wins):
    1. URL domain → ATS platform detection
    2. URL domain → job board detection
    3. JSON-LD @type == "JobPosting" → JOB_POSTING
    4. URL path pattern → posting vs listing heuristic
    5. Page title / H1 → discard signals, listing signals
    6. HTML structure → link density for listing detection
    7. Fallback → IRRELEVANT
    """

    def classify(
        self,
        url: str,
        html: str = "",
        fetch_html: bool = True,
    ) -> ClassificationResult:
        """
        Classifies a page into a PageType for crawl routing.

        Args:
            url: The URL of the page.
            html: Raw HTML content (empty string if not yet fetched).
            fetch_html: Not used here; presence of html string is sufficient.

        Returns:
            ClassificationResult with page_type, confidence, and optional sub_type.
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path

        # ---------------------------------------------------------------
        # 1. ATS platform detection by URL domain (highest confidence)
        # ---------------------------------------------------------------
        for pattern, ats_name in _ATS_URL_PATTERNS:
            if pattern.search(domain):
                # If path suggests an individual job (e.g. /jobs/12345), it's a posting
                if any(pat.search(path) for pat in _POSTING_PATH_PATTERNS):
                    return ClassificationResult(
                        page_type=PageType.JOB_POSTING,
                        confidence=0.92,
                        matched_signals=[f"ats_url:{ats_name}", "posting_path"],
                        failed_signals=[],
                        is_valid_job=True,
                        sub_type=ats_name,
                    )
                # Otherwise it's an ATS listing page
                return ClassificationResult(
                    page_type=PageType.ATS_CAREER_PAGE,
                    confidence=0.95,
                    matched_signals=[f"ats_url:{ats_name}"],
                    failed_signals=[],
                    is_valid_job=False,
                    sub_type=ats_name,
                )

        # ---------------------------------------------------------------
        # 2. Known job board domain detection
        # ---------------------------------------------------------------
        for jb_domain in _JOB_BOARD_DOMAINS:
            if jb_domain in domain:
                return ClassificationResult(
                    page_type=PageType.JOB_BOARD,
                    confidence=0.90,
                    matched_signals=[f"job_board:{jb_domain}"],
                    failed_signals=[],
                    is_valid_job=False,
                    sub_type=jb_domain,
                )

        # ---------------------------------------------------------------
        # From here we need HTML for confident classification
        # ---------------------------------------------------------------
        if not html:
            # No HTML: use path heuristics only
            return self._classify_by_path_only(url, path)

        soup = BeautifulSoup(html, "html.parser")

        # ---------------------------------------------------------------
        # 3. JSON-LD @type == "JobPosting" → definitive posting
        # ---------------------------------------------------------------
        if self._has_job_posting_jsonld(html):
            return ClassificationResult(
                page_type=PageType.JOB_POSTING,
                confidence=0.97,
                matched_signals=["jsonld_job_posting"],
                failed_signals=[],
                is_valid_job=True,
            )

        # ---------------------------------------------------------------
        # 4. Discard signals in title/H1
        # ---------------------------------------------------------------
        page_title = (soup.title.string or "").lower() if soup.title else ""
        h1_text = " ".join(h.get_text(strip=True) for h in soup.find_all("h1")).lower()
        header_text = page_title + " " + h1_text

        for kw in _DISCARD_TITLE_KEYWORDS:
            if kw in header_text:
                page_type = self._infer_discard_type(kw)
                return ClassificationResult(
                    page_type=page_type,
                    confidence=0.88,
                    matched_signals=[f"discard_title:{kw}"],
                    failed_signals=[],
                    is_valid_job=False,
                    rejected_reason=f"Page title/H1 contains discard keyword: '{kw}'",
                )

        # ---------------------------------------------------------------
        # 5. Listing signals in title/H1
        # ---------------------------------------------------------------
        for kw in _LISTING_TITLE_KEYWORDS:
            if kw in header_text:
                return ClassificationResult(
                    page_type=PageType.COMPANY_CAREERS_HOME,
                    confidence=0.80,
                    matched_signals=[f"listing_title:{kw}"],
                    failed_signals=[],
                    is_valid_job=False,
                )

        # ---------------------------------------------------------------
        # 6. Path-based posting detection
        # ---------------------------------------------------------------
        if any(pat.search(path) for pat in _POSTING_PATH_PATTERNS):
            # Double-check: if the page also has many job links, it's a listing
            job_link_count = self._count_job_links(soup)
            if job_link_count >= 5:
                return ClassificationResult(
                    page_type=PageType.JOB_LISTING_PAGE,
                    confidence=0.75,
                    matched_signals=["posting_path", f"many_job_links:{job_link_count}"],
                    failed_signals=[],
                    is_valid_job=False,
                )
            return ClassificationResult(
                page_type=PageType.JOB_POSTING,
                confidence=0.78,
                matched_signals=["posting_path"],
                failed_signals=[],
                is_valid_job=True,
            )

        # ---------------------------------------------------------------
        # 7. Path-based listing detection
        # ---------------------------------------------------------------
        path_lower = path.lower()
        if any(path_lower.startswith(sig) or path_lower == sig.rstrip("/") for sig in _LISTING_PATH_SIGNALS):
            job_link_count = self._count_job_links(soup)
            if job_link_count >= 3:
                return ClassificationResult(
                    page_type=PageType.JOB_LISTING_PAGE,
                    confidence=0.80,
                    matched_signals=["listing_path", f"job_links:{job_link_count}"],
                    failed_signals=[],
                    is_valid_job=False,
                )

        # ---------------------------------------------------------------
        # 8. Link density check for careers home
        # ---------------------------------------------------------------
        job_link_count = self._count_job_links(soup)
        if job_link_count >= 5:
            return ClassificationResult(
                page_type=PageType.COMPANY_CAREERS_HOME,
                confidence=0.70,
                matched_signals=[f"high_job_link_density:{job_link_count}"],
                failed_signals=[],
                is_valid_job=False,
            )

        # ---------------------------------------------------------------
        # 9. Fallback → IRRELEVANT
        # ---------------------------------------------------------------
        return ClassificationResult(
            page_type=PageType.IRRELEVANT,
            confidence=0.55,
            matched_signals=[],
            failed_signals=["no_signals_matched"],
            is_valid_job=False,
            rejected_reason="No recognisable job page signals found",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _has_job_posting_jsonld(html: str) -> bool:
        """Checks if page contains a JSON-LD block with @type == JobPosting."""
        pattern = re.compile(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            re.DOTALL | re.IGNORECASE
        )
        for content in pattern.findall(html):
            try:
                data = json.loads(content.strip())
                items = data if isinstance(data, list) else [data]
                if isinstance(data, dict) and "@graph" in data:
                    items = data["@graph"]
                for item in items:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        return True
            except Exception:
                continue
        return False

    @staticmethod
    def _count_job_links(soup: BeautifulSoup) -> int:
        """Counts links whose href or text looks like an individual job posting."""
        _job_href_re = re.compile(
            r"/(jobs?|careers?|openings?|positions?|roles?|apply)/[\w\-%]{3,}",
            re.IGNORECASE
        )
        count = 0
        for a in soup.find_all("a", href=True):
            if _job_href_re.search(a["href"]):
                count += 1
        return count

    @staticmethod
    def _classify_by_path_only(url: str, path: str) -> ClassificationResult:
        """Fallback classification using only the URL path when no HTML is available."""
        path_lower = path.lower()
        for pat in _POSTING_PATH_PATTERNS:
            if pat.search(path_lower):
                return ClassificationResult(
                    page_type=PageType.JOB_POSTING,
                    confidence=0.60,
                    matched_signals=["posting_path_only"],
                    failed_signals=[],
                    is_valid_job=True,
                )
        if any(path_lower.startswith(sig) for sig in _LISTING_PATH_SIGNALS):
            return ClassificationResult(
                page_type=PageType.JOB_LISTING_PAGE,
                confidence=0.55,
                matched_signals=["listing_path_only"],
                failed_signals=[],
                is_valid_job=False,
            )
        return ClassificationResult(
            page_type=PageType.IRRELEVANT,
            confidence=0.50,
            matched_signals=[],
            failed_signals=["no_html_no_path_match"],
            is_valid_job=False,
            rejected_reason="Could not classify without HTML",
        )

    @staticmethod
    def _infer_discard_type(keyword: str) -> PageType:
        """Maps a discard keyword to the most specific PageType."""
        blog_kws = {"blog", "news", "press release", "tutorial"}
        doc_kws = {"documentation", "docs"}
        if keyword in blog_kws:
            return PageType.BLOG
        if keyword in doc_kws:
            return PageType.DOCUMENTATION
        return PageType.IRRELEVANT
