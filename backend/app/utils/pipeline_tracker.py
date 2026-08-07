import contextvars
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

# Global context variable for tracking current search session
current_tracker = contextvars.ContextVar("current_tracker", default=None)

class PipelineTracker:
    def __init__(self):
        self.start_time = time.time()
        self.total_duration = 0.0
        
        # Stage timings
        self.stage_durations: Dict[str, float] = {}
        self.stage_start_times: Dict[str, float] = {}

        # Raw events for structured JSON logging
        self.events: List[Dict[str, Any]] = []

        # Stage 1: Search Engine Discovery
        # query -> engine -> { "returned": List[str], "discarded": List[str], "unique": List[str] }
        self.stage1_discovery: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Stage 2: Candidate URL Summary (grouped by domain/provider)
        self.stage2_candidates: Dict[str, List[str]] = {}

        # Stage 3: Crawl Scheduler Decisions
        # url -> { "provider": str, "priority": float, "position": int, "scheduled": bool, "reason": str }
        self.stage3_scheduler: Dict[str, Dict[str, Any]] = {}
        # provider -> { "allocated": int, "skipped_company_cap": int, "overflow": int, "reason": str }
        self.stage3_allocations: Dict[str, Dict[str, Any]] = {}

        # Stage 4: Crawl / Fetch outcomes
        # url -> { "status_code": int, "duration": float, "error": str, "playwright_used": bool }
        self.stage4_fetches: Dict[str, Dict[str, Any]] = {}

        # Stage 5: Job Extraction Outcomes
        # url -> { "success": bool, "extractor": str, "duration": float, "error": str }
        self.stage5_extractions: Dict[str, Dict[str, Any]] = {}

        # Stage 6 & 7: Deduplication, Filtering & Persistence Decisions
        # url -> { "accepted": bool, "reason": str, "score": float }
        self.filtering_decisions: Dict[str, Dict[str, Any]] = {}
        # url -> { "status": str, "duplicate_of_url": str, "details": str }
        self.persistence_decisions: Dict[str, Dict[str, Any]] = {}

        # Listing/Drilldown relationship
        # listing_url -> List[job_urls]
        self.drill_downs: Dict[str, List[str]] = {}

    @staticmethod
    def get_provider_name(url: str) -> str:
        """Categorizes a URL into a provider domain/platform name."""
        if not url:
            return "Unknown"
        domain = urlparse(url).netloc.lower()
        if "linkedin.com" in domain:
            return "LinkedIn"
        if "greenhouse.io" in domain:
            return "Greenhouse"
        if "lever.co" in domain:
            return "Lever"
        if "ashbyhq.com" in domain:
            return "Ashby"
        if "myworkdayjobs.com" in domain:
            return "Workday"
        if "smartrecruiters.com" in domain:
            return "SmartRecruiters"
        if "indeed.com" in domain:
            return "Indeed"
        if "glassdoor.com" in domain:
            return "Glassdoor"
        if "ziprecruiter.com" in domain:
            return "ZipRecruiter"
        if "upwork.com" in domain:
            return "Upwork"
        if "infopark.in" in domain or "infopark" in domain:
            return "Infopark"
        if "technopark.org" in domain or "technopark" in domain:
            return "Technopark"
        if "naukri.com" in domain:
            return "Naukri"
        
        parts = domain.split('.')
        if len(parts) >= 2:
            return parts[-2].capitalize()
        return domain or "Unknown"

    def start_stage(self, stage_name: str):
        self.stage_start_times[stage_name] = time.time()
        self._add_event("stage_started", {"stage": stage_name})

    def end_stage(self, stage_name: str):
        start = self.stage_start_times.get(stage_name)
        if start:
            dur = time.time() - start
            self.stage_durations[stage_name] = dur
            self._add_event("stage_completed", {"stage": stage_name, "duration_s": dur})

    def complete(self):
        self.total_duration = time.time() - self.start_time
        self._add_event("pipeline_completed", {"total_duration_s": self.total_duration})

    def _add_event(self, event_type: str, payload: Dict[str, Any]):
        event = {
            "timestamp": time.time() - self.start_time,
            "type": event_type,
            **payload
        }
        self.events.append(event)

    def record_discovery(self, query: str, engine: str, returned_urls: List[str]):
        if query not in self.stage1_discovery:
            self.stage1_discovery[query] = {}
        
        seen = set()
        unique = []
        discarded = []
        for u in returned_urls:
            if u not in seen:
                seen.add(u)
                unique.append(u)
            else:
                discarded.append(u)
        
        self.stage1_discovery[query][engine] = {
            "returned": returned_urls,
            "discarded": discarded,
            "unique": unique
        }
        
        self._add_event("urls_discovered", {
            "query": query,
            "engine": engine,
            "count": len(returned_urls),
            "unique": len(unique),
            "discarded_duplicates": len(discarded)
        })

    def record_candidate(self, url: str):
        prov = self.get_provider_name(url)
        if prov not in self.stage2_candidates:
            self.stage2_candidates[prov] = []
        self.stage2_candidates[prov].append(url)
        self._add_event("candidate_registered", {"url": url, "provider": prov})

    def record_scheduler_decision(self, url: str, priority: float, position: int, scheduled: bool, reason: str):
        prov = self.get_provider_name(url)
        self.stage3_scheduler[url] = {
            "provider": prov,
            "priority": priority,
            "position": position,
            "scheduled": scheduled,
            "reason": reason
        }
        self._add_event("scheduler_decision", {
            "url": url,
            "provider": prov,
            "priority": priority,
            "position": position,
            "scheduled": scheduled,
            "reason": reason
        })

    def record_scheduler_allocation(
        self, 
        provider: str, 
        allocated_count: int, 
        skipped_count: int, 
        overflow_count: int, 
        reason: str
    ):
        """Records per-provider SWRR budget allocation metrics."""
        self.stage3_allocations[provider] = {
            "allocated": allocated_count,
            "skipped_company_cap": skipped_count,
            "overflow": overflow_count,
            "reason": reason,
        }
        self._add_event("scheduler_allocation", {
            "provider": provider,
            "allocated": allocated_count,
            "skipped_company_cap": skipped_count,
            "overflow": overflow_count,
            "reason": reason,
        })

    def record_fetch(self, url: str, status_code: Optional[int], duration: float, error: Optional[str] = None, playwright_used: bool = False):
        prov = self.get_provider_name(url)
        self.stage4_fetches[url] = {
            "provider": prov,
            "status_code": status_code,
            "duration": duration,
            "error": error,
            "playwright_used": playwright_used
        }
        self._add_event("page_fetched", {
            "url": url,
            "provider": prov,
            "status_code": status_code,
            "duration_s": duration,
            "error": error,
            "playwright_used": playwright_used
        })

    def record_classification(self, url: str, page_type: str, confidence: float, matched_signals: List[str], reason: Optional[str] = None):
        self._add_event("page_classified", {
            "url": url,
            "page_type": page_type,
            "confidence": confidence,
            "matched_signals": matched_signals,
            "reason": reason
        })

    def record_drill_down(self, listing_url: str, job_urls: List[str]):
        self.drill_downs[listing_url] = job_urls
        self._add_event("drill_down_extracted", {
            "listing_url": listing_url,
            "job_urls_count": len(job_urls)
        })

    def record_extraction(self, url: str, success: bool, extractor: Optional[str], duration: float, error: Optional[str] = None):
        prov = self.get_provider_name(url)
        self.stage5_extractions[url] = {
            "provider": prov,
            "success": success,
            "extractor": extractor,
            "duration": duration,
            "error": error
        }
        self._add_event("job_extracted", {
            "url": url,
            "provider": prov,
            "success": success,
            "extractor": extractor,
            "duration_s": duration,
            "error": error
        })

    def record_filtering(self, url: str, title: str, company: str, location: str, accepted: bool, reason: str, score: float = 0.0):
        prov = self.get_provider_name(url)
        self.filtering_decisions[url] = {
            "provider": prov,
            "title": title,
            "company": company,
            "location": location,
            "accepted": accepted,
            "reason": reason,
            "score": score
        }
        self._add_event("filtering_decision", {
            "url": url,
            "provider": prov,
            "title": title,
            "company": company,
            "location": location,
            "accepted": accepted,
            "reason": reason,
            "score": score
        })

    def record_persistence(self, url: str, status: str, duplicate_of_url: Optional[str] = None, details: Optional[str] = None):
        prov = self.get_provider_name(url)
        self.persistence_decisions[url] = {
            "provider": prov,
            "status": status,
            "duplicate_of_url": duplicate_of_url,
            "details": details
        }
        self._add_event("persistence_decision", {
            "url": url,
            "provider": prov,
            "status": status,
            "duplicate_of_url": duplicate_of_url,
            "details": details
        })
