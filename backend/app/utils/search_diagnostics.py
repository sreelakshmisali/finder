"""
Search Discovery Diagnostics Framework (v1.0)

Provides a 100% passive, context-aware observability suite for job discovery pipelines.
Tracks search_session_id, global S1-S7 stages, provider P1-P4 internal stages, query.limit usage audits,
and exports structured JSON traces for empirical evidence gathering.
"""

import contextvars
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Task/Thread-local storage for current search session diagnostics
current_diagnostics: contextvars.ContextVar[Optional["SearchDiagnosticsTracker"]] = contextvars.ContextVar(
    "current_diagnostics", default=None
)


@dataclass
class ProviderInternalStats:
    """Tracks P1-P4 internal discovery stages for an individual provider."""
    source_name: str
    display_name: str
    priority: int = 100
    enabled: bool = True
    p1_target_searched: int = 0
    p2_raw_fetched: int = 0
    p3_internal_rejected: int = 0
    p4_returned_to_aggregator: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    search_urls: List[str] = field(default_factory=list)
    rejection_reasons: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "display_name": self.display_name,
            "priority": self.priority,
            "enabled": self.enabled,
            "duration_s": round(self.duration, 3),
            "stages": {
                "P1_target_searched": self.p1_target_searched,
                "P2_raw_fetched": self.p2_raw_fetched,
                "P3_internal_rejected": self.p3_internal_rejected,
                "P4_returned_to_aggregator": self.p4_returned_to_aggregator,
            },
            "rejection_reasons": self.rejection_reasons,
            "search_urls": self.search_urls,
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
    variable_name: str
    applied_limit: int
    input_size: int
    output_size: int
    effect: str

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
        self.deduplication_pairs: Dict[str, int] = {}
        self.returned_urls_by_provider: Dict[str, List[str]] = {}
        self.returned_jobs_by_provider: Dict[str, int] = {}

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

    def record_provider_stage(
        self,
        source_name: str,
        p1_searched: Optional[int] = None,
        p2_fetched: Optional[int] = None,
        p3_rejected: Optional[int] = None,
        p4_returned: Optional[int] = None,
        search_url: Optional[str] = None,
        rejection_reason: Optional[str] = None
    ):
        pstats = self.provider_stats.get(source_name)
        if not pstats:
            return

        if p1_searched is not None:
            pstats.p1_target_searched += p1_searched
        if p2_fetched is not None:
            pstats.p2_raw_fetched += p2_fetched
        if p3_rejected is not None:
            pstats.p3_internal_rejected += p3_rejected
        if p4_returned is not None:
            pstats.p4_returned_to_aggregator += p4_returned
        if search_url and search_url not in pstats.search_urls:
            pstats.search_urls.append(search_url)
        if rejection_reason:
            pstats.rejection_reasons[rejection_reason] = pstats.rejection_reasons.get(rejection_reason, 0) + 1

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
        effect: str
    ):
        self.limit_audits.append(
            LimitAuditEntry(
                provider=provider,
                location=location,
                variable_name=variable_name,
                applied_limit=applied_limit,
                input_size=input_size,
                output_size=output_size,
                effect=effect
            )
        )

    def record_deduplication_pair(self, provider_a: str, provider_b: str, count: int = 1):
        pair_key = f"{provider_a} ↔ {provider_b}"
        self.deduplication_pairs[pair_key] = self.deduplication_pairs.get(pair_key, 0) + count

    def finish_session(
        self,
        returned_urls_by_provider: Dict[str, List[str]],
        returned_jobs_by_provider: Dict[str, int]
    ):
        self.total_duration = max(time.time() - self.start_time, 0.001)
        self.returned_urls_by_provider = returned_urls_by_provider
        self.returned_jobs_by_provider = returned_jobs_by_provider

        # Calculate stage time percentages
        for s in self.global_stages.values():
            s.percentage_of_total = (s.duration / self.total_duration) * 100.0

        # Print console diagnostic report
        self.print_console_report()

        # Save structured JSON artifact
        self.save_json_artifact()

    def print_console_report(self):
        """Prints Phase 1 console report with session ID and verifiable stage transformations."""
        if not getattr(settings, "SEARCH_DIAGNOSTICS_ENABLED", True):
            return

        lines = []
        lines.append("=" * 65)
        lines.append(f"SEARCH DISCOVERY DIAGNOSTICS [Session {self.session_id}]")
        lines.append("=" * 65)
        lines.append(f"Query: {self.query}")
        lines.append(f"Location: {self.location or 'Any'}")
        lines.append(f"Remote Only: {self.remote_only}")
        lines.append(f"Requested Limit: {self.limit}")
        lines.append(f"Total Execution Time: {self.total_duration:.2f}s")
        lines.append("")

        # 1. Registered Providers
        lines.append("-" * 65)
        lines.append("REGISTERED PROVIDERS")
        lines.append("-" * 65)
        for idx, p in enumerate(self.registered_providers, 1):
            status = "✓ Enabled" if p.get("enabled", True) else "✗ Disabled"
            lines.append(f"{idx}. {p.get('display_name', p.get('source_name')):<20} Priority: {p.get('priority', 100):<4} Status: {status}")
        lines.append("")

        # 2. Per Provider Internal Stages (P1 - P4) & Timeline
        lines.append("-" * 65)
        lines.append("PER-PROVIDER INTERNAL STAGES (P1 - P4) & TIMELINE")
        lines.append("-" * 65)
        for source, pstat in self.provider_stats.items():
            lines.append(f"Provider: {pstat.display_name} (Priority {pstat.priority}) [{pstat.duration:.2f}s]")
            lines.append(f"  P1 Target Searched:        {pstat.p1_target_searched}")
            lines.append(f"  P2 Raw Fetched/Extracted:   {pstat.p2_raw_fetched}")
            lines.append(f"  P3 Internal Rejected:      {pstat.p3_internal_rejected}")
            if pstat.rejection_reasons:
                lines.append(f"     Breakdown: {pstat.rejection_reasons}")
            lines.append(f"  P4 Returned To Aggregator: {pstat.p4_returned_to_aggregator}")
            if pstat.search_urls:
                lines.append(f"  Search Endpoints ({len(pstat.search_urls)}):")
                for u in pstat.search_urls[:3]:
                    lines.append(f"    - {u}")
                if len(pstat.search_urls) > 3:
                    lines.append(f"    - ... (+{len(pstat.search_urls) - 3} more)")
            lines.append("")

        # 3. Running Aggregation Progress
        lines.append("-" * 65)
        lines.append("RUNNING AGGREGATION PROGRESS")
        lines.append("-" * 65)
        for step in self.running_aggregation:
            lines.append(f"After {step['provider']:<18}: +{step['newly_added']:<3} jobs -> Cumulative Total: {step['cumulative_total']}")
        lines.append("")

        # 4. Global Pipeline Stages (S1 - S7)
        lines.append("-" * 65)
        lines.append("GLOBAL PIPELINE STAGE TRANSFORMATIONS (S1 - S7)")
        lines.append("-" * 65)
        for sid in ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]:
            stage = self.global_stages.get(sid)
            if stage:
                lines.append(
                    f"[{stage.stage_id}] {stage.stage_name:<35} | "
                    f"Input: {stage.input_count:<4} | Delta: {stage.delta_count:<4} | "
                    f"Output: {stage.output_count:<4} | Time: {stage.duration:.2f}s ({stage.percentage_of_total:.1f}%)"
                )
        lines.append("")

        # 5. `query.limit` Code Path Audit
        lines.append("-" * 65)
        lines.append("LIMIT USAGE AUDIT (query.limit / slicing locations)")
        lines.append("-" * 65)
        if self.limit_audits:
            for entry in self.limit_audits:
                lines.append(
                    f"Location: {entry.location:<25} | Provider: {entry.provider:<15} | "
                    f"Var: {entry.variable_name}={entry.applied_limit:<2} | Effect: Input {entry.input_size} -> Output {entry.output_size}"
                )
        else:
            lines.append("No explicit per-provider limit caps triggered during this run.")
        lines.append("")

        # 6. Final Provider Contribution Report
        lines.append("=" * 65)
        lines.append("FINAL PROVIDER CONTRIBUTION")
        lines.append("=" * 65)
        total_discovered = sum(p.p2_raw_fetched for p in self.provider_stats.values())
        total_returned = sum(self.returned_jobs_by_provider.values())
        for source, pstat in self.provider_stats.items():
            returned = self.returned_jobs_by_provider.get(source, 0)
            lines.append(f"{pstat.display_name:<20} Discovered: {pstat.p2_raw_fetched:<4} | Returned: {returned:<4}")
        lines.append(f"TOTAL                Discovered: {total_discovered:<4} | Returned: {total_returned:<4}")
        lines.append("=" * 65)

        logger.info("\n" + "\n".join(lines))

    def save_json_artifact(self) -> Optional[str]:
        """Saves complete structured JSON trace to backend/logs/search_diagnostics/."""
        try:
            log_dir = os.path.join("backend", "logs", "search_diagnostics")
            os.makedirs(log_dir, exist_ok=True)

            slug_query = "".join(c if c.isalnum() else "_" for c in self.query.strip().lower())
            slug_query = slug_query[:30] or "search"
            filename = f"{self.session_id}_{slug_query}.json"
            filepath = os.path.join(log_dir, filename)

            payload = {
                "search_session_id": self.session_id,
                "search_context": {
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
                "provider_internal_stages": {
                    source: pstat.to_dict() for source, pstat in self.provider_stats.items()
                },
                "running_aggregation": self.running_aggregation,
                "global_pipeline_stages": {
                    sid: stage.to_dict() for sid, stage in self.global_stages.items()
                },
                "deduplication_pairs": self.deduplication_pairs,
                "limit_audits": [entry.to_dict() for entry in self.limit_audits],
                "final_provider_contribution": {
                    source: {
                        "discovered": self.provider_stats[source].p2_raw_fetched if source in self.provider_stats else 0,
                        "returned": self.returned_jobs_by_provider.get(source, 0),
                        "returned_urls": self.returned_urls_by_provider.get(source, [])
                    }
                    for source in self.provider_stats
                }
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

            logger.info(f"[SearchDiagnostics] Diagnostic JSON saved: {filepath}")
            return filepath
        except Exception as exc:
            logger.warning(f"[SearchDiagnostics] Failed to save JSON artifact: {exc}")
            return None
