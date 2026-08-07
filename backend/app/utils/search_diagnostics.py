"""
Complete Search Discovery Diagnostics & Pipeline Tracing Framework (v1.0)

Provides a 100% passive, context-aware observability suite for job discovery pipelines.
Tracks search_session_id, per-job lifecycle traces, global S1-S7 stages, provider P1-P4 internal stages,
query.limit audits, ranking attribution, normalization comparisons, and root-cause indicators.
"""

import contextvars
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from statistics import median

from app.core.config import settings

logger = logging.getLogger(__name__)

# Task/Thread-local storage for current search session diagnostics
current_diagnostics: contextvars.ContextVar[Optional["SearchDiagnosticsTracker"]] = contextvars.ContextVar(
    "current_diagnostics", default=None
)


@dataclass
class JobLifecycleTrace:
    """Tracks complete end-to-end lifecycle trace for a single discovered job."""
    trace_id: str
    provider: str
    provider_priority: int
    company: str
    title: str
    source_url: str
    discovery_provider: str = ""
    ats_source: str = ""
    apply_url: Optional[str] = None
    location: str = ""
    remote: bool = False
    normalized_title: str = ""
    normalized_company: str = ""
    normalized_skills: List[str] = field(default_factory=list)
    has_description: bool = False
    description_length: int = 0
    detected_technologies: List[str] = field(default_factory=list)
    detected_domains: List[str] = field(default_factory=list)

    lifecycle_stages: List[str] = field(default_factory=lambda: ["DISCOVERED"])
    stage_status: Dict[str, str] = field(default_factory=dict)
    rejection_stage: Optional[str] = None
    rejection_category: Optional[str] = None
    rejection_details: Optional[Dict[str, Any]] = None

    score_breakdown: Optional[Dict[str, Any]] = None
    relevance_score: Optional[float] = None
    final_rank: Optional[int] = None
    duplication_survived_by: Optional[str] = None

    def advance_stage(self, stage_name: str, status: str = "PASSED", details: Optional[Dict[str, Any]] = None):
        if stage_name not in self.lifecycle_stages:
            self.lifecycle_stages.append(stage_name)
        self.stage_status[stage_name] = status
        if status in ("REJECTED", "DROPPED"):
            self.rejection_stage = stage_name
            if details:
                self.rejection_details = details
                if "category" in details:
                    self.rejection_category = details["category"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "provider": self.provider,
            "discovery_provider": self.discovery_provider or self.provider,
            "ats_source": self.ats_source or self.provider,
            "provider_priority": self.provider_priority,
            "company": self.company,
            "title": self.title,
            "source_url": self.source_url,
            "apply_url": self.apply_url,
            "location": self.location,
            "remote": self.remote,
            "normalized_metadata": {
                "title": self.normalized_title,
                "company": self.normalized_company,
                "skills_count": len(self.normalized_skills),
                "has_description": self.has_description,
                "description_length": self.description_length,
                "technologies": self.detected_technologies,
                "domains": self.detected_domains,
            },
            "lifecycle_stages": self.lifecycle_stages,
            "stage_status": self.stage_status,
            "rejection_stage": self.rejection_stage,
            "rejection_category": self.rejection_category,
            "rejection_details": self.rejection_details,
            "relevance_score": self.relevance_score,
            "score_breakdown": self.score_breakdown,
            "final_rank": self.final_rank,
            "duplication_survived_by": self.duplication_survived_by,
        }


@dataclass
class ProviderInternalStats:
    """Tracks P1-P4 internal discovery stages for an individual provider."""
    source_name: str
    display_name: str
    priority: int = 100
    enabled: bool = True
    p1_target_searched: int = 0
    p1_targets_successful: int = 0
    p1_targets_zero_jobs: int = 0
    p1_targets_with_jobs: int = 0
    p2_raw_fetched: int = 0
    p2_extracted: int = 0
    p2_extraction_failures: int = 0
    p3_internal_rejected: int = 0
    p4_returned_to_aggregator: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    search_urls: List[str] = field(default_factory=list)
    rejection_reasons: Dict[str, int] = field(default_factory=dict)
    rejection_traces: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "display_name": self.display_name,
            "priority": self.priority,
            "enabled": self.enabled,
            "duration_s": round(self.duration, 3),
            "stages": {
                "P1_targets_requested": self.p1_target_searched,
                "P1_targets_successful": self.p1_targets_successful,
                "P1_targets_zero_jobs": self.p1_targets_zero_jobs,
                "P1_targets_with_jobs": self.p1_targets_with_jobs,
                "P2_raw_fetched": self.p2_raw_fetched,
                "P2_extracted": self.p2_extracted,
                "P2_extraction_failures": self.p2_extraction_failures,
                "P3_internal_rejected": self.p3_internal_rejected,
                "P4_returned_to_aggregator": self.p4_returned_to_aggregator,
            },
            "rejection_reasons": self.rejection_reasons,
            "search_urls": self.search_urls,
            "sample_rejections": self.rejection_traces[:10],
        }


@dataclass
class GlobalStageStats:
    """Tracks verifiable S1-S7 global pipeline stage transformations and execution timing."""
    stage_id: str
    stage_name: str
    input_count: int = 0
    output_count: int = 0
    delta_count: int = 0
    start_time: float = 0.0
    duration: float = 0.0
    percentage_of_total: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "stage_name": self.stage_name,
            "input_count": self.input_count,
            "output_count": self.output_count,
            "delta_count": self.delta_count,
            "duration_s": round(self.duration, 3),
            "percentage_of_total": round(self.percentage_of_total, 1),
            "details": self.details,
        }


@dataclass
class LimitAuditEntry:
    """Records explicit code locations where limit/slicing variables are evaluated."""
    provider: str
    location: str
    expression: str
    variable_name: str
    applied_limit: int
    input_size: int
    output_size: int
    stage: str
    effect: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeduplicationRecord:
    """Detailed record of a single duplicate removal decision."""
    losing_trace_id: str
    surviving_trace_id: str
    losing_provider: str
    surviving_provider: str
    losing_url: str
    surviving_url: str
    rule_triggered: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SearchDiagnosticsTracker:
    """
    Main passive diagnostics orchestrator for a single search session.
    """

    def __init__(
        self,
        query: str,
        location: str = "",
        remote_only: bool = False,
        limit: int = 50,
        session_id: Optional[str] = None
    ):
        now = datetime.now(timezone.utc)
        time_str = now.strftime("%Y%m%d-%H%M%S")
        rand_suffix = uuid.uuid4().hex[:6]
        self.session_id = session_id or f"{time_str}-{rand_suffix}"

        self.query = query
        self.location = location
        self.remote_only = remote_only
        self.limit = limit
        self.start_time = time.time()
        self.total_duration = 0.0

        self.registered_providers: List[Dict[str, Any]] = []
        self.provider_stats: Dict[str, ProviderInternalStats] = {}
        self.global_stages: Dict[str, GlobalStageStats] = {}
        self.running_aggregation: List[Dict[str, Any]] = []
        self.limit_audits: List[LimitAuditEntry] = []

        # Job lifecycle tracing
        self.job_traces: Dict[str, JobLifecycleTrace] = {}
        self.url_to_trace_id: Dict[str, str] = {}

        # Deduplication tracking
        self.deduplication_records: List[DeduplicationRecord] = []
        self.deduplication_pairs: Dict[str, int] = {}

        # Ranking diagnostics
        self.ranking_records: List[Dict[str, Any]] = []
        self.ranking_rejection_categories: Dict[str, int] = {}

        # Final response tracking
        self.returned_urls_by_provider: Dict[str, List[str]] = {}
        self.returned_jobs_by_provider: Dict[str, int] = {}
        self.returned_job_explanations: List[Dict[str, Any]] = []

    def log(self, message: str):
        """Helper to prefix logs with search_session_id."""
        logger.info(f"[Session {self.session_id[:13]}] {message}")

    def audit_registered_providers(self, active_providers_meta: List[Dict[str, Any]]):
        """Records initial provider registry configuration."""
        self.registered_providers = active_providers_meta

    def start_provider(self, source_name: str, display_name: str, priority: int = 100, enabled: bool = True):
        if source_name not in self.provider_stats:
            self.provider_stats[source_name] = ProviderInternalStats(
                source_name=source_name,
                display_name=display_name,
                priority=priority,
                enabled=enabled,
                start_time=time.time()
            )

    def get_or_create_job_trace(
        self,
        provider: str,
        title: str,
        company: str,
        url: str,
        location: str = "",
        remote: bool = False,
        apply_url: Optional[str] = None,
        discovery_provider: Optional[str] = None,
        ats_source: Optional[str] = None
    ) -> JobLifecycleTrace:
        norm_url = url.strip()
        if norm_url in self.url_to_trace_id:
            trace = self.job_traces[self.url_to_trace_id[norm_url]]
            if discovery_provider and not trace.discovery_provider:
                trace.discovery_provider = discovery_provider
            if ats_source and not trace.ats_source:
                trace.ats_source = ats_source
            return trace

        disc_prov = discovery_provider or provider
        ats_src = ats_source or provider
        trace_id = f"{disc_prov}-{uuid.uuid4().hex[:8]}"
        pstat = self.provider_stats.get(disc_prov)
        priority = pstat.priority if pstat else 100

        trace = JobLifecycleTrace(
            trace_id=trace_id,
            provider=disc_prov,
            discovery_provider=disc_prov,
            ats_source=ats_src,
            provider_priority=priority,
            company=company,
            title=title,
            source_url=norm_url,
            apply_url=apply_url,
            location=location,
            remote=remote,
        )
        self.job_traces[trace_id] = trace
        self.url_to_trace_id[norm_url] = trace_id
        return trace

    def record_provider_stage(
        self,
        source_name: str,
        p1_searched: Optional[int] = None,
        p1_targets_successful: Optional[int] = None,
        p1_targets_zero_jobs: Optional[int] = None,
        p1_targets_with_jobs: Optional[int] = None,
        p2_fetched: Optional[int] = None,
        p2_extracted: Optional[int] = None,
        p2_extraction_failures: Optional[int] = None,
        p3_rejected: Optional[int] = None,
        p4_returned: Optional[int] = None,
        search_url: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        rejected_job_info: Optional[Dict[str, Any]] = None
    ):
        pstats = self.provider_stats.get(source_name)
        if not pstats:
            return

        if p1_searched is not None:
            pstats.p1_target_searched += p1_searched
        if p1_targets_successful is not None:
            pstats.p1_targets_successful += p1_targets_successful
        if p1_targets_zero_jobs is not None:
            pstats.p1_targets_zero_jobs += p1_targets_zero_jobs
        if p1_targets_with_jobs is not None:
            pstats.p1_targets_with_jobs += p1_targets_with_jobs

        if p2_fetched is not None:
            pstats.p2_raw_fetched += p2_fetched
        if p2_extracted is not None:
            pstats.p2_extracted += p2_extracted
        if p2_extraction_failures is not None:
            pstats.p2_extraction_failures += p2_extraction_failures

        if p3_rejected is not None:
            pstats.p3_internal_rejected += p3_rejected
        if p4_returned is not None:
            pstats.p4_returned_to_aggregator += p4_returned

        if search_url and search_url not in pstats.search_urls:
            pstats.search_urls.append(search_url)

        if rejection_reason:
            pstats.rejection_reasons[rejection_reason] = pstats.rejection_reasons.get(rejection_reason, 0) + 1

        if rejected_job_info:
            pstats.rejection_traces.append(rejected_job_info)

    def finish_provider(self, source_name: str, returned_count: int):
        pstats = self.provider_stats.get(source_name)
        if pstats:
            pstats.end_time = time.time()
            pstats.duration = max(pstats.end_time - pstats.start_time, 0.0)
            if pstats.p4_returned_to_aggregator == 0:
                pstats.p4_returned_to_aggregator = returned_count

    def record_global_stage(
        self,
        stage_id: str,
        stage_name: str,
        input_count: int,
        output_count: int,
        delta_count: int,
        duration: float,
        details: Optional[Dict[str, Any]] = None
    ):
        self.global_stages[stage_id] = GlobalStageStats(
            stage_id=stage_id,
            stage_name=stage_name,
            input_count=input_count,
            output_count=output_count,
            delta_count=delta_count,
            start_time=time.time() - duration,
            duration=duration,
            details=details or {}
        )

    def record_running_aggregation(self, provider_name: str, newly_added: int, cumulative_total: int):
        self.running_aggregation.append({
            "provider": provider_name,
            "newly_added": newly_added,
            "cumulative_total": cumulative_total,
            "timestamp": time.time() - self.start_time
        })

    def record_limit_audit(
        self,
        provider: str,
        location: str,
        variable_name: str,
        applied_limit: int,
        input_size: int,
        output_size: int,
        effect: str,
        expression: str = "",
        stage: str = "provider_internal"
    ):
        self.limit_audits.append(
            LimitAuditEntry(
                provider=provider,
                location=location,
                expression=expression or f"slicing[{variable_name}]",
                variable_name=variable_name,
                applied_limit=applied_limit,
                input_size=input_size,
                output_size=output_size,
                stage=stage,
                effect=effect
            )
        )

    def record_deduplication(
        self,
        losing_job_url: str,
        surviving_job_url: str,
        losing_provider: str,
        surviving_provider: str,
        rule_triggered: str
    ):
        losing_trace_id = self.url_to_trace_id.get(losing_job_url.strip(), "unknown")
        surviving_trace_id = self.url_to_trace_id.get(surviving_job_url.strip(), "unknown")

        record = DeduplicationRecord(
            losing_trace_id=losing_trace_id,
            surviving_trace_id=surviving_trace_id,
            losing_provider=losing_provider,
            surviving_provider=surviving_provider,
            losing_url=losing_job_url,
            surviving_url=surviving_job_url,
            rule_triggered=rule_triggered
        )
        self.deduplication_records.append(record)

        pair_key = f"{surviving_provider} ↔ {losing_provider}"
        self.deduplication_pairs[pair_key] = self.deduplication_pairs.get(pair_key, 0) + 1

        if losing_trace_id in self.job_traces:
            trace = self.job_traces[losing_trace_id]
            trace.advance_stage("DEDUPLICATION", "REJECTED", {
                "category": "duplicate_job",
                "survived_by_trace_id": surviving_trace_id,
                "survived_by_url": surviving_job_url,
                "rule_triggered": rule_triggered
            })
            trace.duplication_survived_by = surviving_trace_id

    def record_ranking_result(
        self,
        job: Any,
        result: Any,
        search_context: Any
    ):
        norm_url = job.url.strip() if hasattr(job, "url") else ""
        disc_prov = getattr(job, "discovery_provider", None) or getattr(job, "source", "unknown")
        ats_src = getattr(job, "source", "unknown")

        trace = self.get_or_create_job_trace(
            provider=disc_prov,
            title=getattr(job, "title", ""),
            company=getattr(job, "company", ""),
            url=norm_url,
            location=getattr(job, "location", ""),
            remote=getattr(job, "remote", False),
            apply_url=getattr(job, "apply_url", None),
            discovery_provider=disc_prov,
            ats_source=ats_src
        )

        trace.relevance_score = result.score.total
        trace.score_breakdown = {
            "title_score": result.score.breakdown.title,
            "skills_score": result.score.breakdown.skills,
            "description_score": result.score.breakdown.description,
            "location_score": result.score.breakdown.location,
            "penalties": result.score.breakdown.penalties,
            "weighted_total": result.score.total,
            "confidence": result.score.confidence,
            "role_similarity": getattr(result.explanation, "role_similarity", 0.5),
            "matched_domains": getattr(result.explanation, "matched_domains", []),
            "conflicting_domains": getattr(result.explanation, "conflicting_domains", []),
            "matched_technologies": getattr(result.explanation, "matched_technologies", []),
        }

        rejection_cat = None
        if not result.accepted:
            if getattr(result.explanation, "conflicting_domains", []):
                rejection_cat = "intent_domain_mismatch"
            elif result.score.breakdown.title < 10.0:
                rejection_cat = "insufficient_title_match"
            elif result.score.breakdown.penalties < 0:
                rejection_cat = "domain_penalty_conflict"
            else:
                rejection_cat = "low_final_score"

            self.ranking_rejection_categories[rejection_cat] = self.ranking_rejection_categories.get(rejection_cat, 0) + 1
            trace.advance_stage("RELEVANCE_RANKING", "REJECTED", {
                "category": rejection_cat,
                "score": result.score.total,
                "reasons": result.reasons
            })
        else:
            trace.advance_stage("RELEVANCE_RANKING", "PASSED")

        rec = {
            "trace_id": trace.trace_id,
            "provider": disc_prov,
            "discovery_provider": disc_prov,
            "ats_source": ats_src,
            "company": trace.company,
            "title": trace.title,
            "url": norm_url,
            "score": result.score.total,
            "accepted": result.accepted,
            "rejection_category": rejection_cat,
            "reasons": result.reasons,
            "score_breakdown": trace.score_breakdown,
        }
        self.ranking_records.append(rec)

    def finish_session(
        self,
        returned_urls_by_provider: Dict[str, List[str]],
        returned_jobs_by_provider: Dict[str, int]
    ):
        self.total_duration = max(time.time() - self.start_time, 0.001)
        self.returned_urls_by_provider = returned_urls_by_provider
        self.returned_jobs_by_provider = returned_jobs_by_provider

        # Populate final ranks and passed status on returned job traces
        rank_counter = 1
        for prov_urls in returned_urls_by_provider.values():
            for u in prov_urls:
                norm_u = u.strip()
                if norm_u in self.url_to_trace_id:
                    t_id = self.url_to_trace_id[norm_u]
                    trace = self.job_traces[t_id]
                    trace.final_rank = rank_counter
                    trace.advance_stage("FINAL_RESPONSE", "PASSED")
                    rank_counter += 1

        # Calculate stage time percentages
        for s in self.global_stages.values():
            s.percentage_of_total = (s.duration / self.total_duration) * 100.0

        # Print console diagnostic report
        self.print_console_report()

        # Save structured JSON artifact
        self.save_json_artifact()

    def calculate_normalization_comparison(self) -> Dict[str, Dict[str, Any]]:
        """Calculates provider-by-provider metadata completeness percentages."""
        stats: Dict[str, Dict[str, Any]] = {}
        for trace in self.job_traces.values():
            p = trace.provider
            if p not in stats:
                stats[p] = {
                    "total": 0, "has_title": 0, "has_desc": 0,
                    "has_skills": 0, "has_location": 0, "has_remote": 0,
                    "has_company": 0, "has_apply_url": 0
                }
            s = stats[p]
            s["total"] += 1
            if trace.title: s["has_title"] += 1
            if trace.has_description or trace.description_length > 0: s["has_desc"] += 1
            if trace.normalized_skills: s["has_skills"] += 1
            if trace.location: s["has_location"] += 1
            if trace.remote: s["has_remote"] += 1
            if trace.company: s["has_company"] += 1
            if trace.apply_url: s["has_apply_url"] += 1

        res: Dict[str, Dict[str, Any]] = {}
        for p, s in stats.items():
            tot = max(s["total"], 1)
            res[p] = {
                "total_jobs": s["total"],
                "pct_title": round((s["has_title"] / tot) * 100, 1),
                "pct_description": round((s["has_desc"] / tot) * 100, 1),
                "pct_required_skills": round((s["has_skills"] / tot) * 100, 1),
                "pct_location": round((s["has_location"] / tot) * 100, 1),
                "pct_remote": round((s["has_remote"] / tot) * 100, 1),
                "pct_company": round((s["has_company"] / tot) * 100, 1),
                "pct_apply_url": round((s["has_apply_url"] / tot) * 100, 1),
            }
        return res

    def calculate_provider_ranking_comparison(self) -> Dict[str, Dict[str, Any]]:
        """Calculates provider-by-provider score distribution and acceptance rates."""
        by_prov: Dict[str, List[float]] = {}
        by_prov_acc: Dict[str, Dict[str, int]] = {}

        for rec in self.ranking_records:
            p = rec["provider"]
            if p not in by_prov:
                by_prov[p] = []
                by_prov_acc[p] = {"entered": 0, "accepted": 0, "rejected": 0}

            sc = rec["score"]
            by_prov[p].append(sc)
            by_prov_acc[p]["entered"] += 1
            if rec["accepted"]:
                by_prov_acc[p]["accepted"] += 1
            else:
                by_prov_acc[p]["rejected"] += 1

        res: Dict[str, Dict[str, Any]] = {}
        for p, counts in by_prov_acc.items():
            scores = by_prov.get(p, [])
            ent = max(counts["entered"], 1)
            res[p] = {
                "entered": counts["entered"],
                "accepted": counts["accepted"],
                "rejected": counts["rejected"],
                "acceptance_pct": round((counts["accepted"] / ent) * 100, 1),
                "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
                "median_score": round(median(scores), 2) if scores else 0.0,
                "min_score": round(min(scores), 2) if scores else 0.0,
                "max_score": round(max(scores), 2) if scores else 0.0,
            }
        return res

    def derive_root_cause_indicators(self) -> List[Dict[str, str]]:
        """Auto-derives evidence-based root cause indicators based on actual execution metrics."""
        indicators = []

        # Indicator 1: Per-provider internal cap
        for entry in self.limit_audits:
            if entry.input_size > entry.applied_limit and entry.output_size == entry.applied_limit:
                indicators.append({
                    "status": "CONFIRMED",
                    "code": "PROVIDER_INTERNAL_CAP_TRIGGERED",
                    "message": f"Provider '{entry.provider}' hit internal cap query.limit={entry.applied_limit} at {entry.location} (Input: {entry.input_size} -> Output: {entry.output_size})"
                })

        # Indicator 2: Relevance Rejection Ratio
        total_entered_ranking = len(self.ranking_records)
        total_rejected_ranking = sum(1 for r in self.ranking_records if not r["accepted"])
        if total_entered_ranking > 0:
            rej_pct = (total_rejected_ranking / total_entered_ranking) * 100
            if rej_pct > 70:
                indicators.append({
                    "status": "CONFIRMED",
                    "code": "HIGH_RELEVANCE_REJECTION_RATE",
                    "message": f"Intent Matching Engine rejected {total_rejected_ranking}/{total_entered_ranking} ({rej_pct:.1f}%) candidate jobs entering ranking"
                })

        # Indicator 3: Global Slicing vs Ranking Input
        s6 = self.global_stages.get("S6")
        if s6 and s6.input_count <= self.limit:
            indicators.append({
                "status": "CONFIRMED",
                "code": "GLOBAL_LIMIT_NOT_RESTRICTING",
                "message": f"Final global response limit (LIMIT={self.limit}) did NOT cut off results because only {s6.input_count} accepted jobs reached S6"
            })

        # Indicator 4: Zero Deduplication Drops
        s4 = self.global_stages.get("S4")
        if s4 and s4.delta_count == 0:
            indicators.append({
                "status": "CONFIRMED",
                "code": "ZERO_CROSS_PROVIDER_DEDUPLICATION",
                "message": "Cross-provider deduplication removed 0 jobs across all candidate providers"
            })

        return indicators

    def print_console_report(self):
        """Prints complete console diagnostic report matching all 13 required sections."""
        if not getattr(settings, "SEARCH_DIAGNOSTICS_ENABLED", True):
            return

        lines = []
        lines.append("=" * 70)
        lines.append(f"SEARCH DISCOVERY DIAGNOSTICS [Session {self.session_id}]")
        lines.append("=" * 70)
        lines.append(f"Query: {self.query}")
        lines.append(f"Location: {self.location or 'Any'}")
        lines.append(f"Remote Only: {self.remote_only}")
        lines.append(f"Requested Limit: {self.limit}")
        lines.append(f"Total Execution Time: {self.total_duration:.2f}s")
        lines.append("")

        # 1. Registered Providers Audit
        lines.append("-" * 70)
        lines.append("1. REGISTERED PROVIDERS")
        lines.append("-" * 70)
        for idx, p in enumerate(self.registered_providers, 1):
            status = "✓ Enabled" if p.get("enabled", True) else "✗ Disabled"
            lines.append(f"{idx}. {p.get('display_name', p.get('source_name')):<22} Priority: {p.get('priority', 100):<4} Status: {status}")
        lines.append("")

        # 2. Provider Execution Timeline & Concurrency
        lines.append("-" * 70)
        lines.append("2. PROVIDER EXECUTION TIMELINE")
        lines.append("-" * 70)
        for source, pstat in self.provider_stats.items():
            lines.append(f"{pstat.display_name:<20} | Duration: {pstat.duration:.2f}s | Priority: {pstat.priority}")
        lines.append("")

        # 3. Per-Provider Internal Stages (P1 - P4)
        lines.append("-" * 70)
        lines.append("3. PER-PROVIDER INTERNAL STAGES (P1 - P4)")
        lines.append("-" * 70)
        for source, pstat in self.provider_stats.items():
            lines.append(f"Provider: {pstat.display_name}")
            lines.append(f"  P1 Targets Searched:       {pstat.p1_target_searched}")
            lines.append(f"  P2 Raw Fetched/Extracted:  {pstat.p2_raw_fetched}")
            lines.append(f"  P3 Internal Filtered:      {pstat.p3_internal_rejected}")
            if pstat.rejection_reasons:
                lines.append(f"     Breakdown: {pstat.rejection_reasons}")
            lines.append(f"  P4 Returned To Aggregator: {pstat.p4_returned_to_aggregator}")
            lines.append("")

        # 4. Limit Usage Audit
        lines.append("-" * 70)
        lines.append("4. LIMIT USAGE AUDIT (query.limit / slicing code paths)")
        lines.append("-" * 70)
        if self.limit_audits:
            for entry in self.limit_audits:
                lines.append(
                    f"Location: {entry.location:<22} | Prov: {entry.provider:<15} | "
                    f"Limit: {entry.applied_limit:<2} | Input: {entry.input_size} -> Output: {entry.output_size}"
                )
        else:
            lines.append("No explicit limit caps triggered.")
        lines.append("")

        # 5. Running Aggregation Progress
        lines.append("-" * 70)
        lines.append("5. RUNNING AGGREGATION PROGRESS")
        lines.append("-" * 70)
        for step in self.running_aggregation:
            lines.append(f"After {step['provider']:<18}: +{step['newly_added']:<3} jobs -> Cumulative Total: {step['cumulative_total']}")
        lines.append("")

        # 6. Cross-Provider Deduplication Summary
        lines.append("-" * 70)
        lines.append("6. CROSS-PROVIDER DEDUPLICATION SUMMARY")
        lines.append("-" * 70)
        s4 = self.global_stages.get("S4")
        if s4:
            lines.append(f"Input: {s4.input_count} | Duplicates Removed: {s4.delta_count} | Output: {s4.output_count}")
        if self.deduplication_pairs:
            lines.append("Deduplication Pairwise Matrix:")
            for pair, count in self.deduplication_pairs.items():
                lines.append(f"  {pair}: {count}")
        else:
            lines.append("Zero cross-provider duplicates detected.")
        lines.append("")

        # 7. Global Pipeline Stages (S1 - S7)
        lines.append("-" * 70)
        lines.append("7. GLOBAL PIPELINE STAGES (S1 - S7)")
        lines.append("-" * 70)
        for sid in ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]:
            stage = self.global_stages.get(sid)
            if stage:
                lines.append(
                    f"[{stage.stage_id}] {stage.stage_name:<35} | "
                    f"Input: {stage.input_count:<4} | Delta: {stage.delta_count:<4} | "
                    f"Output: {stage.output_count:<4} | Time: {stage.duration:.2f}s ({stage.percentage_of_total:.1f}%)"
                )
        lines.append("")

        # 8. Provider Ranking Comparison Table
        lines.append("-" * 70)
        lines.append("8. PROVIDER RANKING COMPARISON & SCORE DISTRIBUTION")
        lines.append("-" * 70)
        rank_comp = self.calculate_provider_ranking_comparison()
        lines.append(f"{'Provider':<18} | {'Entered':<7} | {'Accepted':<8} | {'Rejected':<8} | {'Accept %':<8} | {'Avg Score':<9} | {'Median':<7}")
        lines.append("-" * 70)
        for prov, info in rank_comp.items():
            lines.append(
                f"{prov:<18} | {info['entered']:<7} | {info['accepted']:<8} | {info['rejected']:<8} | "
                f"{info['acceptance_pct']:<7}% | {info['avg_score']:<9} | {info['median_score']:<7}"
            )
        lines.append("")

        # 9. Normalization Comparison Table
        lines.append("-" * 70)
        lines.append("9. METADATA NORMALIZATION COMPARISON (% Completeness)")
        lines.append("-" * 70)
        norm_comp = self.calculate_normalization_comparison()
        lines.append(f"{'Provider':<18} | {'Jobs':<5} | {'Title %':<7} | {'Desc %':<7} | {'Skills %':<8} | {'Loc %':<6} | {'Remote %':<8}")
        lines.append("-" * 70)
        for prov, info in norm_comp.items():
            lines.append(
                f"{prov:<18} | {info['total_jobs']:<5} | {info['pct_title']:<7} | {info['pct_description']:<7} | "
                f"{info['pct_required_skills']:<8} | {info['pct_location']:<6} | {info['pct_remote']:<8}"
            )
        lines.append("")

        # 10. Final Provider Contribution Table
        lines.append("=" * 70)
        lines.append("10. FINAL PROVIDER CONTRIBUTION TABLE")
        lines.append("=" * 70)
        total_discovered = sum(p.p2_raw_fetched for p in self.provider_stats.values())
        total_returned = sum(self.returned_jobs_by_provider.values())
        lines.append(f"{'Provider':<18} | {'Raw':<5} | {'P4 Returned':<11} | {'Ranked Accepted':<15} | {'Final Returned':<14}")
        lines.append("-" * 70)
        for source, pstat in self.provider_stats.items():
            ret = self.returned_jobs_by_provider.get(source, 0)
            r_info = rank_comp.get(source, {})
            acc = r_info.get("accepted", 0)
            lines.append(f"{pstat.display_name:<18} | {pstat.p2_raw_fetched:<5} | {pstat.p4_returned_to_aggregator:<11} | {acc:<15} | {ret:<14}")
        lines.append(f"TOTAL              | {total_discovered:<5} | {sum(p.p4_returned_to_aggregator for p in self.provider_stats.values()):<11} | {sum(r.get('accepted',0) for r in rank_comp.values()):<15} | {total_returned:<14}")
        lines.append("=" * 70)
        lines.append("")

        # 11. Discovery Provider vs ATS Source Attribution
        lines.append("=" * 70)
        lines.append("11. DISCOVERY PROVIDER vs ATS SOURCE")
        lines.append("=" * 70)
        attr_summary = self.calculate_attribution_summary()
        lines.append("DISCOVERY PROVIDER CONTRIBUTION:")
        for dp, c in attr_summary["discovery_provider_counts"].items():
            lines.append(f"  {dp:<25}: {c}")
        lines.append("")
        lines.append("ATS / JOB SOURCE CONTRIBUTION:")
        for ats, c in attr_summary["ats_source_counts"].items():
            lines.append(f"  {ats:<25}: {c}")
        lines.append("")

        # 12. Final Job Attribution Table
        lines.append("-" * 70)
        lines.append("12. FINAL JOB ATTRIBUTION")
        lines.append("-" * 70)
        lines.append(f"{'Rank':<5} | {'Title':<25} | {'Discovery Provider':<20} | {'ATS Source':<12} | {'URL'}")
        lines.append("-" * 70)
        for job_attr in attr_summary["final_job_attribution"]:
            lines.append(
                f"{job_attr['rank']:<5} | {job_attr['title'][:25]:<25} | "
                f"{job_attr['discovery_provider']:<20} | {job_attr['ats_source']:<12} | {job_attr['url'][:45]}"
            )
        lines.append("")

        # 13. Root Cause Indicators
        lines.append("=" * 70)
        lines.append("13. EVIDENCE-BASED ROOT CAUSE INDICATORS")
        lines.append("=" * 70)
        indicators = self.derive_root_cause_indicators()
        if indicators:
            for ind in indicators:
                lines.append(f"[{ind['status']}] {ind['code']}: {ind['message']}")
        else:
            lines.append("No critical pipeline starvation indicators detected.")
        lines.append("=" * 70)

        logger.info("\n" + "\n".join(lines))

    def calculate_attribution_summary(self) -> Dict[str, Any]:
        """Calculates explicit discovery provider vs ATS source attribution breakdown."""
        returned_traces = [t for t in self.job_traces.values() if t.final_rank is not None]
        returned_traces.sort(key=lambda t: t.final_rank or 999)

        disc_counts: Dict[str, int] = {}
        ats_counts: Dict[str, int] = {}
        final_table: List[Dict[str, Any]] = []

        for t in returned_traces:
            dp = t.discovery_provider or t.provider
            ats = t.ats_source or t.provider
            disc_counts[dp] = disc_counts.get(dp, 0) + 1
            ats_counts[ats] = ats_counts.get(ats, 0) + 1
            final_table.append({
                "rank": t.final_rank,
                "title": t.title,
                "company": t.company,
                "discovery_provider": dp,
                "ats_source": ats,
                "url": t.source_url,
                "relevance_score": t.relevance_score
            })

        return {
            "discovery_provider_counts": disc_counts,
            "ats_source_counts": ats_counts,
            "final_job_attribution": final_table
        }

    def save_json_artifact(self) -> Optional[str]:
        """Saves complete structured JSON trace to backend/logs/search_diagnostics/."""
        try:
            log_dir = os.path.join("backend", "logs", "search_diagnostics")
            os.makedirs(log_dir, exist_ok=True)

            slug_query = "".join(c if c.isalnum() else "_" for c in self.query.strip().lower())
            slug_query = slug_query[:30] or "search"
            filename = f"{self.session_id}_{slug_query}.json"
            filepath = os.path.join(log_dir, filename)

            attr_summary = self.calculate_attribution_summary()

            payload = {
                "session": {
                    "search_session_id": self.session_id,
                    "query": self.query,
                    "location": self.location,
                    "remote_only": self.remote_only,
                    "limit": self.limit,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "total_duration_s": round(self.total_duration, 3),
                },
                "runtime_config": {
                    "registered_providers": self.registered_providers,
                    "linkedin_mode": getattr(settings, "LINKEDIN_MODE", "external_only"),
                    "search_diagnostics_enabled": getattr(settings, "SEARCH_DIAGNOSTICS_ENABLED", True),
                },
                "providers": {
                    source: pstat.to_dict() for source, pstat in self.provider_stats.items()
                },
                "provider_timeline": [
                    {
                        "source_name": p.source_name,
                        "display_name": p.display_name,
                        "priority": p.priority,
                        "duration_s": round(p.duration, 3),
                        "start_time": p.start_time,
                        "end_time": p.end_time
                    }
                    for p in self.provider_stats.values()
                ],
                "provider_internal_stages": {
                    source: pstat.to_dict()["stages"] for source, pstat in self.provider_stats.items()
                },
                "limit_audit": [entry.to_dict() for entry in self.limit_audits],
                "aggregation": {
                    "running_progress": self.running_aggregation,
                    "cumulative_final_count": sum(p.p4_returned_to_aggregator for p in self.provider_stats.values())
                },
                "deduplication": {
                    "pairwise_matrix": self.deduplication_pairs,
                    "records": [r.to_dict() for r in self.deduplication_records]
                },
                "ranking": {
                    "rejection_categories": self.ranking_rejection_categories,
                    "provider_comparison": self.calculate_provider_ranking_comparison(),
                    "records": self.ranking_records
                },
                "global_pipeline_stages": {
                    sid: stage.to_dict() for sid, stage in self.global_stages.items()
                },
                "normalization": self.calculate_normalization_comparison(),
                "final_response": {
                    "returned_counts_by_provider": self.returned_jobs_by_provider,
                    "returned_urls_by_provider": self.returned_urls_by_provider
                },
                "attribution_breakdown": {
                    "discovery_provider_counts": attr_summary["discovery_provider_counts"],
                    "ats_source_counts": attr_summary["ats_source_counts"],
                    "final_job_attribution": attr_summary["final_job_attribution"]
                },
                "root_cause_indicators": self.derive_root_cause_indicators(),
                "job_traces": [t.to_dict() for t in self.job_traces.values()]
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

            logger.info(f"[SearchDiagnostics] Complete diagnostic JSON saved: {filepath}")
            return filepath
        except Exception as exc:
            logger.warning(f"[SearchDiagnostics] Failed to save JSON artifact: {exc}")
            return None
