"""
Diversity Scheduler

Allocates crawl budget fairly across providers using Smooth Weighted Round Robin (SWRR).
Enforces a single global company cap.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional

from app.core.scheduler_config import SchedulerConfig, ProviderPriorityConfig
from app.schemas.tagged_url import TaggedURL
from app.utils.pipeline_tracker import current_tracker


@dataclass
class ProviderSWRRState:
    provider: str
    weight: float
    current_weight: float
    budget_remaining: int
    urls: List[TaggedURL]


class DiversityScheduler:
    """Allocates crawl budget using Smooth Weighted Round Robin (SWRR)."""

    def __init__(self, config: SchedulerConfig):
        self.config = config

    def allocate(self, tagged_urls: List[TaggedURL]) -> List[TaggedURL]:
        """
        Interleaves tagged URLs across providers using SWRR until global_crawl_budget (60)
        is reached or all provider budgets/urls are exhausted.
        Enforces global company cap across all providers.
        """
        tracker = current_tracker.get()
        
        # 1. Group URLs by provider and sort each group by priority_score descending
        grouped: Dict[str, List[TaggedURL]] = {}
        for tu in tagged_urls:
            grouped.setdefault(tu.provider, []).append(tu)
            
        for prov in grouped:
            grouped[prov].sort(key=lambda x: x.priority_score, reverse=True)

        default_fallback = ProviderPriorityConfig(priority=6, max_job_pages=10, max_listing_pages=2, weight=1.0)

        # 2. Build SWRR state per provider
        states: List[ProviderSWRRState] = []
        for prov, urls in grouped.items():
            prov_cfg = self.config.provider_priorities.get(
                prov, 
                self.config.provider_priorities.get("generic_board", default_fallback)
            )
            states.append(ProviderSWRRState(
                provider=prov,
                weight=prov_cfg.weight,
                current_weight=0.0,
                budget_remaining=prov_cfg.max_job_pages,
                urls=urls,
            ))

        allocated: List[TaggedURL] = []
        global_company_usage: Dict[str, int] = {}
        
        provider_stats = {
            s.provider: {"allocated": 0, "skipped_company_cap": 0, "overflow": 0}
            for s in states
        }

        # 3. SWRR Allocation Loop
        while len(allocated) < self.config.global_crawl_budget:
            # Active providers must have URLs available and remaining budget
            active = [s for s in states if s.urls and s.budget_remaining > 0]
            if not active:
                break  # Budget automatically redistributes to remaining active providers until all exhausted

            # --- SWRR Core Selection ---
            total_weight = sum(s.weight for s in active)
            for s in active:
                s.current_weight += s.weight
            
            selected_state = max(active, key=lambda s: s.current_weight)
            selected_state.current_weight -= total_weight
            # ---------------------------

            tu = selected_state.urls.pop(0)
            selected_state.budget_remaining -= 1

            # Enforce Global Company Cap
            comp_key = (tu.company or "").strip().lower()
            if comp_key and global_company_usage.get(comp_key, 0) >= self.config.max_jobs_per_company:
                provider_stats[selected_state.provider]["skipped_company_cap"] += 1
                continue

            allocated.append(tu)
            if comp_key:
                global_company_usage[comp_key] = global_company_usage.get(comp_key, 0) + 1
            provider_stats[selected_state.provider]["allocated"] += 1

        for s in states:
            provider_stats[s.provider]["overflow"] = len(s.urls)

        if tracker:
            for prov, stats in provider_stats.items():
                tracker.record_scheduler_allocation(
                    provider=prov,
                    allocated_count=stats["allocated"],
                    skipped_count=stats["skipped_company_cap"],
                    overflow_count=stats["overflow"],
                    reason=f"SWRR allocated (Company cap skips: {stats['skipped_company_cap']})"
                )

        return allocated
