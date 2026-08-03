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

Returns a diversity-allocated list of TaggedURL objects ready for JobExtractor.
"""

import asyncio
import logging
from typing import List, Optional, Any

import httpx

from app.schemas.classification import PageType
from app.schemas.tagged_url import TaggedURL
from app.core.scheduler_config import SchedulerConfig
from app.services.classification.page_type_classifier import PageTypeClassifier
from app.services.crawl.provider_classifier import ProviderClassifier
from app.services.crawl.diversity_scheduler import DiversityScheduler
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
    Candidate URLs -> PageType classification -> Job posting TaggedURL extraction via SWRR.
    """

    def __init__(
        self,
        config: Optional[SchedulerConfig] = None,
        classifier: Optional[PageTypeClassifier] = None,
        job_link_extractor: Optional[JobLinkExtractor] = None,
    ):
        self.config = config or SchedulerConfig.from_env()
        self.classifier = classifier or PageTypeClassifier()
        self.job_link_extractor = job_link_extractor or JobLinkExtractor()
        self.provider_classifier = ProviderClassifier()
        self.diversity_scheduler = DiversityScheduler(self.config)
        self.fetch_timeout = self.config.fetch_timeout
        self.max_concurrent = self.config.max_concurrent_fetches
        self.max_job_urls_per_source = 20

    async def schedule(
        self,
        candidate_urls: List[str],
        global_dedup: Optional[URLDeduplicator] = None,
        target_role: str = "",
        candidate_results: Optional[List[Any]] = None,
    ) -> List[TaggedURL]:
        """
        Processes a list of candidate URLs and returns a diversity-scheduled list of TaggedURLs.
        """
        if not candidate_urls:
            return []

        from app.services.search.candidate_scorer import CandidateScorer
        from app.utils.pipeline_tracker import current_tracker
        tracker = current_tracker.get()

        url_to_result = {r.url: r for r in (candidate_results or []) if hasattr(r, "url")}

        # 1. Score candidate URLs (returns List[(url, score, provider_tag)])
        scored_candidates = CandidateScorer.score_urls(candidate_urls, target_role, self.config)
        scored_dict = {url: (score, tag) for url, score, tag in scored_candidates}

        # 2. Select candidates up to max_candidate_pages
        candidate_urls_to_process = [item[0] for item in scored_candidates[:self.config.max_candidate_pages]]
        skipped_candidates = {item[0]: "Candidate limit reached" for item in scored_candidates[self.config.max_candidate_pages:]}

        if tracker:
            tracker.start_stage("Stage 3 - Crawl Scheduler")
            for url in candidate_urls:
                tracker.record_candidate(url)
            for url, score, _tag in scored_candidates:
                pos = candidate_urls.index(url) + 1 if url in candidate_urls else 0
                if url in skipped_candidates:
                    tracker.record_scheduler_decision(url, score, pos, scheduled=False, reason=skipped_candidates[url])
                else:
                    tracker.record_scheduler_decision(url, score, pos, scheduled=True, reason="Scheduled for crawl")

        dedup = global_dedup or URLDeduplicator()
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # 3. Concurrent processing of candidate URLs with SearchResult inheritance
        async def process_one_candidate(cand_url: str) -> List[TaggedURL]:
            async with semaphore:
                score, parent_prov = scored_dict.get(cand_url, (50, "generic_board"))
                parent_sr = url_to_result.get(cand_url)
                try:
                    child_urls = await self._process_candidate(cand_url, dedup)
                    local_tagged: List[TaggedURL] = []
                    for child_url in child_urls:
                        prov_tag = self.provider_classifier.classify(child_url)
                        comp_name = self.provider_classifier.extract_company_name(child_url, parent_sr)
                        local_tagged.append(TaggedURL(
                            url=child_url,
                            provider=prov_tag,
                            company=comp_name,
                            priority_score=score,
                            source_page=cand_url,
                            search_result=parent_sr
                        ))
                    return local_tagged
                except Exception as exc:
                    logger.warning(f"[CrawlScheduler] Error processing candidate '{cand_url}': {exc}")
                    return []

        tasks = [process_one_candidate(url) for url in candidate_urls_to_process]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        raw_tagged_urls: List[TaggedURL] = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.warning(f"[CrawlScheduler] Error processing candidate: {res}")
            elif isinstance(res, list):
                raw_tagged_urls.extend(res)

        logger.debug(
            f"[CrawlScheduler] SUMMARY: {len(candidate_urls_to_process)} candidates -> "
            f"{len(raw_tagged_urls)} raw job posting URLs extracted before SWRR allocation."
        )

        # 4. Allocate via DiversityScheduler (SWRR + Global Company Cap)
        allocated_tagged_urls = self.diversity_scheduler.allocate(raw_tagged_urls)

        logger.debug(
            f"[CrawlScheduler] SWRR ALLOCATION: {len(allocated_tagged_urls)} job TaggedURLs "
            f"selected (Budget={self.config.global_crawl_budget})."
        )
        logger.info(
            f"[CrawlScheduler] Scheduled {len(candidate_urls_to_process)} candidates -> "
            f"{len(allocated_tagged_urls)} SWRR allocated job TaggedURLs."
        )
        if tracker:
            tracker.end_stage("Stage 3 - Crawl Scheduler")

        return allocated_tagged_urls

    async def _process_candidate(
        self,
        url: str,
        dedup: URLDeduplicator,
    ) -> List[str]:
        """
        Classifies a single candidate URL and routes it to the correct handler.
        """
        from app.utils.pipeline_tracker import current_tracker
        tracker = current_tracker.get()

        # Step 1: URL-only pre-classification (no HTTP fetch yet)
        pre_result = self.classifier.classify(url=url, html="")
        logger.debug(
            f"[CrawlScheduler]   Pre-classify (URL-only): {pre_result.page_type.value} "
            f"conf={pre_result.confidence:.2f} sub={pre_result.sub_type or '-'}"
        )
        if tracker:
            tracker.record_classification(url, pre_result.page_type.value, pre_result.confidence, pre_result.matched_signals, pre_result.rejected_reason)

        # Fast-path discard without fetching
        if pre_result.page_type in _DISCARD_TYPES and pre_result.confidence >= 0.85:
            if tracker and url in tracker.stage3_scheduler:
                tracker.stage3_scheduler[url]["scheduled"] = False
                tracker.stage3_scheduler[url]["reason"] = f"Pre-classify discard: {pre_result.page_type.value}"
            return []

        # Step 2: Fetch HTML
        html = await self._fetch(url)
        if not html:
            if tracker and url in tracker.stage3_scheduler:
                tracker.stage3_scheduler[url]["scheduled"] = False
                fetch_info = tracker.stage4_fetches.get(url, {})
                err_msg = fetch_info.get("error") or f"HTTP status {fetch_info.get('status_code')}"
                tracker.stage3_scheduler[url]["reason"] = f"Fetch failed: {err_msg}"
            return []

        # Step 3: Full classification with HTML
        result = self.classifier.classify(url=url, html=html)
        logger.debug(
            f"[CrawlScheduler]   Full classify: {result.page_type.value} "
            f"conf={result.confidence:.2f} sub={result.sub_type or '-'} "
            f"signals={result.matched_signals}"
        )
        if tracker:
            tracker.record_classification(url, result.page_type.value, result.confidence, result.matched_signals, result.rejected_reason)

        # Step 4: Route based on PageType
        if result.page_type == PageType.JOB_POSTING:
            clean = URLNormalizer.normalize(url)
            if clean and dedup.is_new(clean):
                return [clean]
            if tracker and url in tracker.stage3_scheduler:
                tracker.stage3_scheduler[url]["scheduled"] = False
                tracker.stage3_scheduler[url]["reason"] = "Already crawled or duplicate URL"
            return []

        if result.page_type in _DRILL_DOWN_TYPES:
            return await self._drill_down(url, html, result, dedup)

        reason = result.rejected_reason or result.page_type.value
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

        ats_extractor = get_ats_extractor(page_url)
        if ats_extractor:
            logger.debug(
                f"[CrawlScheduler]   -> Using ATS extractor: '{ats_extractor.ats_name}' "
                f"for: {page_url}"
            )
            raw_links = ats_extractor.extract_job_links(html, page_url, deduplicator=None)
        else:
            raw_links = self.job_link_extractor.extract(
                html, page_url, deduplicator=None,
                max_links=self.max_job_urls_per_source
            )

        if tracker:
            tracker.record_drill_down(page_url, raw_links)

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

        logger.debug(
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
                logger.debug(f"[CrawlScheduler] HTTP {resp.status_code} for: {url}")
        except Exception as exc:
            dur = time.time() - start_time
            if tracker:
                tracker.record_fetch(url, status_code=None, duration=dur, error=str(exc))
            logger.warning(f"[CrawlScheduler] Fetch error for '{url}': {exc}")
        return None
