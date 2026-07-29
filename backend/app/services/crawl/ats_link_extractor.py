"""
ATS Link Extractor

Per-platform dedicated extractors for Applicant Tracking Systems.
Each ATS extractor knows exactly where individual job posting links live
on that platform's listing pages, without relying on generic HTML heuristics.

Supported platforms:
- Greenhouse   (boards.greenhouse.io)
- Lever        (jobs.lever.co)
- Ashby        (jobs.ashbyhq.com)
- Workday      (*.myworkdayjobs.com)
- SmartRecruiters (jobs.smartrecruiters.com)
- Jobvite      (jobs.jobvite.com)
- BambooHR     (*.bamboohr.com)
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from app.services.crawl.url_utils import URLNormalizer, URLDeduplicator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base interface
# ---------------------------------------------------------------------------

class BaseATSExtractor(ABC):
    """
    Abstract base for per-ATS job link extractors.
    Each subclass knows the HTML structure of one specific ATS platform.
    """

    @property
    @abstractmethod
    def ats_name(self) -> str:
        """Unique identifier for this ATS (e.g. 'greenhouse')."""
        pass

    @property
    @abstractmethod
    def domain_pattern(self) -> re.Pattern:
        """Compiled regex that matches the ATS's domain."""
        pass

    def matches_url(self, url: str) -> bool:
        """Returns True if this extractor handles the given URL."""
        return bool(self.domain_pattern.search(urlparse(url).netloc.lower()))

    @abstractmethod
    def extract_job_links(
        self,
        html: str,
        page_url: str,
        deduplicator: Optional[URLDeduplicator] = None,
    ) -> List[str]:
        """
        Extracts individual job posting URLs from an ATS listing page.

        Args:
            html: Raw HTML of the ATS career listing page.
            page_url: The URL of the listing page for resolving relative links.
            deduplicator: Shared deduplicator to avoid returning already-seen URLs.

        Returns:
            List of absolute individual job posting URLs.
        """
        pass


# ---------------------------------------------------------------------------
# Greenhouse
# ---------------------------------------------------------------------------

class GreenhouseATSExtractor(BaseATSExtractor):
    """
    Extracts individual job URLs from Greenhouse boards pages.
    Pattern: boards.greenhouse.io/{company} or boards.eu.greenhouse.io/{company}

    Individual job links have the form: /jobs/{numeric_id}
    """

    ats_name = "greenhouse"
    domain_pattern = re.compile(r"boards(\.[a-z]+)?\.greenhouse\.io", re.IGNORECASE)

    def extract_job_links(
        self,
        html: str,
        page_url: str,
        deduplicator: Optional[URLDeduplicator] = None,
    ) -> List[str]:
        if not html:
            return []

        dedup = deduplicator or URLDeduplicator()
        soup = BeautifulSoup(html, "html.parser")
        base = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"
        results: List[str] = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            # Greenhouse job links end with /jobs/{id}
            if re.search(r"/jobs/\d+", href):
                clean = URLNormalizer.normalize(href, base)
                if clean and dedup.is_new(clean):
                    results.append(clean)
                    logger.debug(f"[Greenhouse] Found job link: {clean}")

        logger.debug(f"[Greenhouse] Extracted {len(results)} job links from '{page_url}'")
        return results


# ---------------------------------------------------------------------------
# Lever
# ---------------------------------------------------------------------------

class LeverATSExtractor(BaseATSExtractor):
    """
    Extracts individual job URLs from Lever job listing pages.
    Pattern: jobs.lever.co/{company}

    Individual job links have class 'posting-title' or href matching /jobs.lever.co/{co}/{uuid}
    """

    ats_name = "lever"
    domain_pattern = re.compile(r"jobs\.lever\.co", re.IGNORECASE)

    def extract_job_links(
        self,
        html: str,
        page_url: str,
        deduplicator: Optional[URLDeduplicator] = None,
    ) -> List[str]:
        if not html:
            return []

        dedup = deduplicator or URLDeduplicator()
        soup = BeautifulSoup(html, "html.parser")
        base = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"
        results: List[str] = []

        # Lever renders jobs as <a class="posting-title" href="...">
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            css_class = " ".join(a_tag.get("class", []))

            is_posting_link = (
                "posting-title" in css_class
                or re.search(r"jobs\.lever\.co/[\w\-]+/[\w\-]{8,}", href)
            )

            if is_posting_link:
                clean = URLNormalizer.normalize(href, base)
                if clean and dedup.is_new(clean):
                    results.append(clean)
                    logger.debug(f"[Lever] Found job link: {clean}")

        logger.debug(f"[Lever] Extracted {len(results)} job links from '{page_url}'")
        return results


# ---------------------------------------------------------------------------
# Ashby
# ---------------------------------------------------------------------------

class AshbyATSExtractor(BaseATSExtractor):
    """
    Extracts individual job URLs from Ashby HQ listing pages.
    Pattern: jobs.ashbyhq.com/{company}

    Individual job links match /jobs/{slug}
    """

    ats_name = "ashby"
    domain_pattern = re.compile(r"jobs\.ashbyhq\.com", re.IGNORECASE)

    def extract_job_links(
        self,
        html: str,
        page_url: str,
        deduplicator: Optional[URLDeduplicator] = None,
    ) -> List[str]:
        if not html:
            return []

        dedup = deduplicator or URLDeduplicator()
        soup = BeautifulSoup(html, "html.parser")
        base = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"
        results: List[str] = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            # Ashby job links: /jobs/{uuid-or-slug}
            if re.search(r"/jobs/[\w\-]{4,}", href):
                clean = URLNormalizer.normalize(href, base)
                if clean and dedup.is_new(clean):
                    results.append(clean)
                    logger.debug(f"[Ashby] Found job link: {clean}")

        logger.debug(f"[Ashby] Extracted {len(results)} job links from '{page_url}'")
        return results


# ---------------------------------------------------------------------------
# Workday
# ---------------------------------------------------------------------------

class WorkdayATSExtractor(BaseATSExtractor):
    """
    Extracts individual job URLs from Workday ATS pages.
    Pattern: {company}.myworkdayjobs.com

    Individual job links contain /job/{slug}
    """

    ats_name = "workday"
    domain_pattern = re.compile(r"\.myworkdayjobs\.com", re.IGNORECASE)

    def extract_job_links(
        self,
        html: str,
        page_url: str,
        deduplicator: Optional[URLDeduplicator] = None,
    ) -> List[str]:
        if not html:
            return []

        dedup = deduplicator or URLDeduplicator()
        soup = BeautifulSoup(html, "html.parser")
        base = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"
        results: List[str] = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if re.search(r"/job/[\w%\-]+", href):
                clean = URLNormalizer.normalize(href, base)
                if clean and dedup.is_new(clean):
                    results.append(clean)
                    logger.debug(f"[Workday] Found job link: {clean}")

        logger.debug(f"[Workday] Extracted {len(results)} job links from '{page_url}'")
        return results


# ---------------------------------------------------------------------------
# SmartRecruiters
# ---------------------------------------------------------------------------

class SmartRecruitersATSExtractor(BaseATSExtractor):
    """
    Extracts individual job URLs from SmartRecruiters pages.
    Pattern: jobs.smartrecruiters.com/{company}
    """

    ats_name = "smartrecruiters"
    domain_pattern = re.compile(r"jobs\.smartrecruiters\.com", re.IGNORECASE)

    def extract_job_links(
        self,
        html: str,
        page_url: str,
        deduplicator: Optional[URLDeduplicator] = None,
    ) -> List[str]:
        if not html:
            return []

        dedup = deduplicator or URLDeduplicator()
        soup = BeautifulSoup(html, "html.parser")
        base = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"
        results: List[str] = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            has_job_id = a_tag.get("data-job-id") or a_tag.get("data-id")
            if has_job_id or re.search(r"/[\w\-]+/[\w\-]{8,}", href):
                clean = URLNormalizer.normalize(href, base)
                if clean and dedup.is_new(clean):
                    results.append(clean)
                    logger.debug(f"[SmartRecruiters] Found job link: {clean}")

        logger.debug(f"[SmartRecruiters] Extracted {len(results)} job links from '{page_url}'")
        return results


# ---------------------------------------------------------------------------
# Jobvite
# ---------------------------------------------------------------------------

class JobviteATSExtractor(BaseATSExtractor):
    """
    Extracts individual job URLs from Jobvite pages.
    Pattern: jobs.jobvite.com/{company}
    """

    ats_name = "jobvite"
    domain_pattern = re.compile(r"jobs\.jobvite\.com", re.IGNORECASE)

    def extract_job_links(
        self,
        html: str,
        page_url: str,
        deduplicator: Optional[URLDeduplicator] = None,
    ) -> List[str]:
        if not html:
            return []

        dedup = deduplicator or URLDeduplicator()
        soup = BeautifulSoup(html, "html.parser")
        base = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"
        results: List[str] = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if re.search(r"/job/[\w\-]+", href):
                clean = URLNormalizer.normalize(href, base)
                if clean and dedup.is_new(clean):
                    results.append(clean)
                    logger.debug(f"[Jobvite] Found job link: {clean}")

        logger.debug(f"[Jobvite] Extracted {len(results)} job links from '{page_url}'")
        return results


# ---------------------------------------------------------------------------
# BambooHR
# ---------------------------------------------------------------------------

class BambooHRATSExtractor(BaseATSExtractor):
    """
    Extracts individual job URLs from BambooHR pages.
    Pattern: {company}.bamboohr.com/careers
    """

    ats_name = "bamboohr"
    domain_pattern = re.compile(r"\.bamboohr\.com", re.IGNORECASE)

    def extract_job_links(
        self,
        html: str,
        page_url: str,
        deduplicator: Optional[URLDeduplicator] = None,
    ) -> List[str]:
        if not html:
            return []

        dedup = deduplicator or URLDeduplicator()
        soup = BeautifulSoup(html, "html.parser")
        base = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"
        results: List[str] = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if re.search(r"/careers/\d+", href) or re.search(r"/jobs/\d+", href):
                clean = URLNormalizer.normalize(href, base)
                if clean and dedup.is_new(clean):
                    results.append(clean)
                    logger.debug(f"[BambooHR] Found job link: {clean}")

        logger.debug(f"[BambooHR] Extracted {len(results)} job links from '{page_url}'")
        return results


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# Ordered list of all ATS extractors — checked in sequence for each URL
ALL_ATS_EXTRACTORS: List[BaseATSExtractor] = [
    GreenhouseATSExtractor(),
    LeverATSExtractor(),
    AshbyATSExtractor(),
    WorkdayATSExtractor(),
    SmartRecruitersATSExtractor(),
    JobviteATSExtractor(),
    BambooHRATSExtractor(),
]


def get_ats_extractor(url: str) -> Optional[BaseATSExtractor]:
    """
    Returns the matching ATS extractor for a given URL, or None if not recognised.
    """
    for extractor in ALL_ATS_EXTRACTORS:
        if extractor.matches_url(url):
            return extractor
    return None
