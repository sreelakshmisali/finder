"""
Crawl Scheduler

Two-stage pipeline orchestrator for the Search Engine Discovery provider.

Stage 1: Classify each candidate URL (search engine result) into a PageType.
Stage 2: Route to the appropriate handler:
  - JOB_POSTING          -> add URL directly to the extraction queue
  - ATS_CAREER_PAGE      -> use ATSLinkExtractor to drill down to individual job URLs
  - JOB_LISTING_PAGE     -> use JobLinkExtractor to drill down to individual job URLs
  - COMPANY_CAREERS_HOME -> use JobLinkExtractor to drill down to individual job URLs
  - JOB_BOARD            -> use JobLinkExtractor (shallow pass only)
  - BLOG/DOCS/HOME/etc.  -> discard

Returns a deduplicated flat list of individual job posting URLs ready for JobExtractor.
"""

import asyncio
import logging
from typing import List, Optional

import httpx

from app.schemas.classification import PageType
from app.services.classification.page_type_classifier import PageTypeClassifier
from app.services.crawl.url_utils import URLNormalizer, URLDeduplicator
from app.services.crawl.job_link_extractor import JobLinkExtractor
from app.services.crawl.ats_link_extractor import get_ats_extractor

logger = logging.getLogger(__name__)

# PageTypes that should be drilled into to find individual job postings
_DRILL_DOWN_TYPES = {
    PageType.ATS_CAREER_PAGE,
    PageType.JOB_LISTING_PAGE,
    PageType.COMPANY_CAREERS_HOME,
    PageType.JOB_BOARD,
    PageType.CAREER_PAGE,  # legacy alias
}

# PageTypes to immediately discard without fetching HTML
_DISCARD_TYPES = {
    PageType.BLOG,
    PageType.DOCUMENTATION,
    PageType.HOME_PAGE,
    PageType.IRRELEVANT,
}


class CrawlScheduler:
    """
    Orchestrates the two-stage crawl pipeline:
    Candidate URLs -> PageType classification -> Job posting URL extraction.
    """

    def __init__(
        self,
        classifier: Optional[PageTypeClassifier] = None,
        job_link_extractor: Optional[JobLinkExtractor] = None,
        fetch_timeout: float = 10.0,
        max_concurrent: int = 10,
        max_job_urls_per_source: int = 20,
    ):
        self.classifier = classifier or PageTypeClassifier()
        self.job_link_extractor = job_link_extractor or JobLinkExtractor()
        self.fetch_timeout = fetch_timeout
        self.max_concurrent = max_concurrent
        self.max_job_urls_per_source = max_job_urls_per_source

    async def schedule(
        self,
        candidate_urls: List[str],
        global_dedup: Optional[URLDeduplicator] = None,
        target_role: str = ""
    ) -> List[str]:
        """
        Processes a list of candidate URLs and returns a flat list of
        individual job posting URLs ready for extraction.
        """
        if not candidate_urls:
            return []
            
        from app.services.search.candidate_scorer import CandidateScorer
        from urllib.parse import urlparse
        import time
        
        # 1. Score candidate URLs
        scored_candidates = CandidateScorer.score_urls(candidate_urls, target_role)
        url_to_score = {url: score for url, score in scored_candidates}
        
        # 2. Group by domain for diversity (Round-Robin)
        domain_groups = {}
        for url, score in scored_candidates:
            netloc = urlparse(url).netloc
            if netloc not in domain_groups:
                domain_groups[netloc] = []
            domain_groups[netloc].append(url)
            
        # Round-robin selection to enforce diversity
        diverse_urls = []
        max_candidate_limit = 50  # Prevent crawling too many candidates overall
        skipped_candidates = {}
        
        iters = max([len(g) for g in domain_groups.values()]) if domain_groups else 0
        for i in range(iters):
            for netloc in list(domain_groups.keys()):
                if i < len(domain_groups[netloc]):
                    url = domain_groups[netloc][i]
                    if len(diverse_urls) < max_candidate_limit:
                        if url not in diverse_urls:
                            diverse_urls.append(url)
                        else:
                            skipped_candidates[url] = "Duplicate URL"
                    else:
                        skipped_candidates[url] = "Candidate limit reached"
                        
        candidate_urls_to_process = diverse_urls[:max_candidate_limit]

        # Record Stage 2 & 3 in tracker
        from app.utils.pipeline_tracker import current_tracker
        tracker = current_tracker.get()
        if tracker:
            tracker.start_stage("Stage 3 - Crawl Scheduler")
            for url in candidate_urls:
                tracker.record_candidate(url)
            for url, score in scored_candidates:
                pos = candidate_urls.index(url) + 1
                if url in skipped_candidates:
                    tracker.record_scheduler_decision(url, score, pos, scheduled=False, reason=skipped_candidates[url])
                elif url not in candidate_urls_to_process:
                    tracker.record_scheduler_decision(url, score, pos, scheduled=False, reason="Candidate limit reached")
                else:
                    tracker.record_scheduler_decision(url, score, pos, scheduled=True, reason="Scheduled for crawl")

        dedup = global_dedup or URLDeduplicator()
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_one(url: str) -> List[str]:
            async with semaphore:
                try:
                    return await self._process_candidate(url, dedup)
                except Exception as exc:
                    print(f"[CrawlScheduler] ERROR processing '{url}': {exc}")
                    logger.warning(f"[CrawlScheduler] Error processing candidate '{url}': {exc}")
                    return []

        tasks = [process_one(url) for url in candidate_urls_to_process]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        job_posting_urls: List[str] = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                print(f"[CrawlScheduler] EXCEPTION for '{candidate_urls_to_process[i]}': {res}")
                logger.warning(f"[CrawlScheduler] Error processing candidate: {res}")
            elif isinstance(res, list):
                job_posting_urls.extend(res)

        print(
            f"\n[CrawlScheduler] SUMMARY: {len(candidate_urls_to_process)} candidates -> "
            f"{len(job_posting_urls)} job posting URLs extracted."
        )
        logger.info(
            f"[CrawlScheduler] Scheduled {len(candidate_urls_to_process)} candidates -> "
            f"{len(job_posting_urls)} job posting URLs extracted."
        )
        if tracker:
            tracker.end_stage("Stage 3 - Crawl Scheduler")
        return job_posting_urls

    async def _process_candidate(
        self,
        url: str,
        dedup: URLDeduplicator,
    ) -> List[str]:
        """
        Classifies a single candidate URL and routes it to the correct handler.
        """
        print(f"\n[CrawlScheduler] Processing candidate: {url}")
        from app.utils.pipeline_tracker import current_tracker
        tracker = current_tracker.get()

        # Step 1: URL-only pre-classification (no HTTP fetch yet)
        pre_result = self.classifier.classify(url=url, html="")
        print(
            f"[CrawlScheduler]   Pre-classify (URL-only): {pre_result.page_type.value} "
            f"conf={pre_result.confidence:.2f} sub={pre_result.sub_type or '-'}"
        )
        if tracker:
            tracker.record_classification(url, pre_result.page_type.value, pre_result.confidence, pre_result.matched_signals, pre_result.rejected_reason)

        # Fast-path discard without fetching
        if pre_result.page_type in _DISCARD_TYPES and pre_result.confidence >= 0.85:
            print(f"[CrawlScheduler]   DISCARD (pre-classify): {pre_result.page_type.value} -> {url}")
            if tracker and url in tracker.stage3_scheduler:
                tracker.stage3_scheduler[url]["scheduled"] = False
                tracker.stage3_scheduler[url]["reason"] = f"Pre-classify discard: {pre_result.page_type.value}"
            return []

        # Step 2: Fetch HTML
        html = await self._fetch(url)
        if not html:
            print(f"[CrawlScheduler]   SKIP: Failed to fetch HTML for: {url}")
            if tracker and url in tracker.stage3_scheduler:
                tracker.stage3_scheduler[url]["scheduled"] = False
                fetch_info = tracker.stage4_fetches.get(url, {})
                err_msg = fetch_info.get("error") or f"HTTP status {fetch_info.get('status_code')}"
                tracker.stage3_scheduler[url]["reason"] = f"Fetch failed: {err_msg}"
            return []
        print(f"[CrawlScheduler]   Fetched HTML: {len(html)} chars")

        # Step 3: Full classification with HTML
        result = self.classifier.classify(url=url, html=html)
        print(
            f"[CrawlScheduler]   Full classify: {result.page_type.value} "
            f"conf={result.confidence:.2f} sub={result.sub_type or '-'} "
            f"signals={result.matched_signals}"
        )
        if tracker:
            tracker.record_classification(url, result.page_type.value, result.confidence, result.matched_signals, result.rejected_reason)

        # Step 4: Route based on PageType
        if result.page_type == PageType.JOB_POSTING:
            # This is already an individual job posting -- add directly
            clean = URLNormalizer.normalize(url)
            if clean and dedup.is_new(clean):
                print(f"[CrawlScheduler]   -> Direct JOB_POSTING: {clean}")
                return [clean]
            print(f"[CrawlScheduler]   -> JOB_POSTING but already seen or invalid: {url}")
            if tracker and url in tracker.stage3_scheduler:
                tracker.stage3_scheduler[url]["scheduled"] = False
                tracker.stage3_scheduler[url]["reason"] = "Already crawled or duplicate URL"
            return []

        if result.page_type in _DRILL_DOWN_TYPES:
            return await self._drill_down(url, html, result, dedup)

        # Everything else -- discard
        reason = result.rejected_reason or result.page_type.value
        print(f"[CrawlScheduler]   DISCARD: {reason} -> {url}")
        if tracker and url in tracker.stage3_scheduler:
            tracker.stage3_scheduler[url]["scheduled"] = False
            tracker.stage3_scheduler[url]["reason"] = f"Classified as {reason}"
        return []

    async def _drill_down(
        self,
        page_url: str,
        html: str,
        classification_result,
        dedup: URLDeduplicator,
    ) -> List[str]:
        """
        Extracts individual job posting URLs from a listing/ATS/career page.
        """
        from app.utils.pipeline_tracker import current_tracker
        tracker = current_tracker.get()

        # Try ATS-specific extractor first (more precise)
        ats_extractor = get_ats_extractor(page_url)
        if ats_extractor:
            print(
                f"[CrawlScheduler]   -> Using ATS extractor: '{ats_extractor.ats_name}' "
                f"for: {page_url}"
            )
            raw_links = ats_extractor.extract_job_links(html, page_url, deduplicator=None)
        else:
            print(f"[CrawlScheduler]   -> Using generic JobLinkExtractor for: {page_url}")
            raw_links = self.job_link_extractor.extract(
                html, page_url, deduplicator=None,
                max_links=self.max_job_urls_per_source
            )

        print(f"[CrawlScheduler]   -> Extractor returned {len(raw_links)} raw links")
        for link in raw_links[:5]:
            print(f"[CrawlScheduler]      {link}")
        if len(raw_links) > 5:
            print(f"[CrawlScheduler]      ... and {len(raw_links) - 5} more")

        if tracker:
            tracker.record_drill_down(page_url, raw_links)

        # Now apply shared dedup for cross-source deduplication
        extracted_urls: List[str] = []
        for link in raw_links[:self.max_job_urls_per_source]:
            clean = URLNormalizer.normalize(link)
            if clean:
                if dedup.is_new(clean):
                    extracted_urls.append(clean)
                    if tracker:
                        tracker.record_scheduler_decision(clean, priority=1.0, position=0, scheduled=True, reason=f"Extracted from {page_url}")
                else:
                    if tracker:
                        tracker.record_scheduler_decision(clean, priority=1.0, position=0, scheduled=False, reason="Duplicate URL (drill-down)")

        print(
            f"[CrawlScheduler]   -> After dedup: {len(extracted_urls)} unique job URLs "
            f"from '{page_url}'"
        )
        return extracted_urls

    async def _fetch(self, url: str) -> Optional[str]:
        """Fetches raw HTML for a URL with timeout and error handling."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        import time
        from app.utils.pipeline_tracker import current_tracker
        tracker = current_tracker.get()
        start_time = time.time()
        try:
            async with httpx.AsyncClient(
                timeout=self.fetch_timeout, follow_redirects=True
            ) as client:
                resp = await client.get(url, headers=headers)
                dur = time.time() - start_time
                if tracker:
                    tracker.record_fetch(url, status_code=resp.status_code, duration=dur)
                if resp.status_code == 200:
                    return resp.text
                print(f"[CrawlScheduler]   HTTP {resp.status_code} for: {url}")
                logger.debug(
                    f"[CrawlScheduler] HTTP {resp.status_code} for: {url}"
                )
        except Exception as exc:
            dur = time.time() - start_time
            if tracker:
                tracker.record_fetch(url, status_code=None, duration=dur, error=str(exc))
            print(f"[CrawlScheduler]   Fetch error: {exc}")
            logger.warning(f"[CrawlScheduler] Fetch error for '{url}': {exc}")
        return None


