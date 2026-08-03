"""
Generic Job Link Extractor

Scans HTML from listing pages (job boards, company career homepages, generic listing pages)
to extract individual job posting URLs. Uses href pattern matching and link text heuristics
rather than any ATS-specific knowledge.
"""

import re
import logging
from typing import List, Set
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from app.services.crawl.url_utils import URLNormalizer, URLDeduplicator

logger = logging.getLogger(__name__)

# Href path segment patterns that indicate an individual job posting link
_JOB_PATH_PATTERNS = [
    re.compile(r"/jobs?/[\w\-]+", re.IGNORECASE),
    re.compile(r"/careers?/[\w\-]+", re.IGNORECASE),
    re.compile(r"/openings?/[\w\-]+", re.IGNORECASE),
    re.compile(r"/positions?/[\w\-]+", re.IGNORECASE),
    re.compile(r"/vacancies?/[\w\-]+", re.IGNORECASE),
    re.compile(r"/role/[\w\-]+", re.IGNORECASE),
    re.compile(r"/apply/[\w\-]+", re.IGNORECASE),
    re.compile(r"/view/[\w\-]+", re.IGNORECASE),       # LinkedIn individual job view
    re.compile(r"/posting/[\w\-]+", re.IGNORECASE),     # Generic posting path
    # Numeric IDs (common in ATS-generated pages)
    re.compile(r"/\d{4,}", re.IGNORECASE),
]


# Link text keywords that strongly suggest a job posting link
_JOB_LINK_TEXT_KEYWORDS = {
    "apply", "view job", "view role", "job details",
    "see details", "learn more", "read more", "full description",
}

# URL fragments / query strings that suggest a search or filter page (not individual posting)
# NOTE: These are checked with substring matching, so be very precise.
# Do NOT add patterns that could match inside legitimate job URLs.
_LISTING_PAGE_SIGNALS = [
    "?q=", "?query=", "?search=", "?keyword=",
    "/search?", "/browse?", "/filter?", "/category/",
]

# Path fragments that indicate a non-job page
_DISCARD_PATH_SIGNALS = [
    "/help/", "/support/", "/login", "/signup", "/register",
    "/about", "/contact", "/terms", "/privacy", "/blog/",
    "/setup-your-business/",
]

# Patterns for SEO listing pages masquerading as job links
_SEO_LISTING_PATTERNS = [
    re.compile(r"-jobs(?:/?\?|/?#|/?$)", re.IGNORECASE),
    re.compile(r"-careers(?:/?\?|/?#|/?$)", re.IGNORECASE),
    re.compile(r"jobs-in-", re.IGNORECASE),
]


# Domains of major job boards -- links TO these from OTHER domains should not be followed.
# But links WITHIN the same domain are fine (e.g. linkedin.com listing -> linkedin.com/jobs/view/...).
_JOB_BOARD_DOMAINS = {
    "indeed.com", "glassdoor.com", "monster.com",
    "naukri.com", "simplyhired.com", "ziprecruiter.com", "dice.com",
    "ycombinator.com",
}


class JobLinkExtractor:
    """
    Extracts individual job posting URLs from HTML listing pages.

    Suitable for:
    - Company /careers homepages
    - Generic job listing pages
    - Job board category/search result pages (shallow pass only)
    """

    def extract(
        self,
        html: str,
        base_url: str,
        deduplicator: URLDeduplicator = None,
        max_links: int = 50,
    ) -> List[str]:
        """
        Parses HTML and returns a deduplicated list of likely individual job posting URLs.

        Args:
            html: Raw HTML content of the listing page.
            base_url: The URL of the listing page (used to resolve relative hrefs).
            deduplicator: Shared URLDeduplicator instance to avoid re-queuing seen URLs.
            max_links: Maximum number of job links to return.

        Returns:
            List of absolute job posting URL strings.
        """
        if not html:
            return []

        dedup = deduplicator or URLDeduplicator()
        soup = BeautifulSoup(html, "html.parser")
        base_domain = urlparse(base_url).netloc.lower()

        job_urls: List[str] = []

        for a_tag in soup.find_all("a", href=True):
            raw_href = a_tag.get("href", "").strip()
            if not raw_href:
                continue

            # Normalize to absolute URL
            clean_url = URLNormalizer.normalize(raw_href, base_url)
            if not clean_url:
                continue

            parsed = urlparse(clean_url)
            link_domain = parsed.netloc.lower()
            path = parsed.path
            full_url_lower = clean_url.lower()

            # Skip external links that go to other job boards (they are listing pages themselves)
            if link_domain != base_domain and any(
                jb in link_domain for jb in _JOB_BOARD_DOMAINS
            ):
                continue

            # Skip if this looks like a search/filter/listing page itself
            if any(sig in full_url_lower for sig in _LISTING_PAGE_SIGNALS):
                continue

            # Skip if this contains discard signals (help, login, etc)
            if any(sig in full_url_lower for sig in _DISCARD_PATH_SIGNALS):
                continue

            # Skip SEO listing pages
            if any(pat.search(full_url_lower) for pat in _SEO_LISTING_PATTERNS):
                continue

            # Check if the href path matches known job posting URL patterns
            is_job_path = any(pat.search(path) for pat in _JOB_PATH_PATTERNS)

            # Check link text for job-related keywords
            link_text = a_tag.get_text(separator=" ", strip=True).lower()
            is_job_text = any(kw in link_text for kw in _JOB_LINK_TEXT_KEYWORDS)

            if not is_job_path and not is_job_text:
                continue

            # Deduplication
            if not dedup.is_new(clean_url):
                continue

            job_urls.append(clean_url)
            logger.debug(f"[JobLinkExtractor] Found job URL: {clean_url}")

            if len(job_urls) >= max_links:
                break

        logger.debug(f"[JobLinkExtractor] Extracted {len(job_urls)} job links from '{base_url}'")
        return job_urls
