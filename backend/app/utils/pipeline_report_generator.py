import json
import os
import logging
from typing import Dict, Any, List
from urllib.parse import urlparse
from app.utils.pipeline_tracker import PipelineTracker

logger = logging.getLogger(__name__)

class PipelineReportGenerator:
    @staticmethod
    def generate_report(tracker: PipelineTracker) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append("                SEARCH DISCOVERY PIPELINE CONVERSION REPORT")
        lines.append("=" * 80)
        lines.append(f"Total Execution Time: {tracker.total_duration:.2f}s\n")

        # --- TIMING METRICS ---
        lines.append("1. Stage Durations")
        lines.append("-" * 30)
        stages_order = [
            ("Stage 1 - Search Discovery", "Stage 1 - Search Engine Discovery"),
            ("Stage 2 - Candidate Processing", "Stage 2 - Candidate Summary"),
            ("Stage 3 - Crawl Scheduler", "Stage 3 - Crawl Scheduler"),
            ("Stage 4 - Fetching", "Stage 4 - Crawl/Fetching"),
            ("Stage 5 - Extraction", "Stage 5 - Job Extraction"),
            ("Stage 6 - Deduplication", "Stage 6 - Deduplication"),
            ("Stage 7 - Persistence", "Stage 7 - Persistence"),
        ]
        for display_name, internal_name in stages_order:
            duration = tracker.stage_durations.get(internal_name, 0.0)
            lines.append(f"{display_name:<30}: {duration:.2f}s")
        lines.append("")

        # Fetch/Extraction Stats
        fetches = list(tracker.stage4_fetches.values())
        avg_fetch = sum(f["duration"] for f in fetches) / len(fetches) if fetches else 0.0
        extractions = list(tracker.stage5_extractions.values())
        avg_extract = sum(e["duration"] for e in extractions) / len(extractions) if extractions else 0.0

        lines.append(f"Average Fetch Time     : {avg_fetch:.2f}s")
        lines.append(f"Average Extraction Time: {avg_extract:.2f}s\n")

        # Slowest pages/domains
        slowest_fetches = sorted(
            [(url, data["duration"], data["provider"]) for url, data in tracker.stage4_fetches.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]

        if slowest_fetches:
            lines.append("Slowest Pages (Top 5)")
            lines.append("-" * 50)
            for url, duration, prov in slowest_fetches:
                lines.append(f"  [{prov}] {duration:.2f}s - {url}")
            lines.append("")

        # --- STAGE FUNNEL & DISCARD REASONS ---
        lines.append("2. Pipeline Stage Funnel & Discard Reasons")
        lines.append("=" * 80)

        # Stage 1: Search Discovery
        total_discovered = 0
        dup_discovered = 0
        for q, engines in tracker.stage1_discovery.items():
            for eng, data in engines.items():
                total_discovered += len(data["returned"])
                dup_discovered += len(data["discarded"])
        
        lines.append("Stage 1 - Search Discovery")
        lines.append(f"  Input (Raw URLs) : {total_discovered}")
        lines.append(f"  Output (Unique)  : {total_discovered - dup_discovered}")
        lines.append(f"  Discarded        : {dup_discovered}")
        if dup_discovered > 0:
            lines.append(f"    - Duplicates: {dup_discovered}")
        lines.append("")

        # Stage 2: Candidate URL Summary (Pre-Crawl)
        lines.append("Stage 2 - Candidate Summary (Pre-Crawl Domain Classification)")
        pre_crawl_counts = {}
        for prov, urls in tracker.stage2_candidates.items():
            pre_crawl_counts[prov] = len(urls)
        for prov, count in sorted(pre_crawl_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  • {prov:<20} : {count}")
        lines.append("")

        # Stage 3: Crawl Scheduler
        sched_decisions = list(tracker.stage3_scheduler.values())
        sched_input = len(sched_decisions)
        sched_output = sum(1 for d in sched_decisions if d["scheduled"])
        sched_discard = sched_input - sched_output

        sched_reasons = {}
        for d in sched_decisions:
            if not d["scheduled"]:
                r = d["reason"] or "Unknown"
                sched_reasons[r] = sched_reasons.get(r, 0) + 1

        lines.append("Stage 3 - Crawl Scheduler")
        lines.append(f"  Input            : {sched_input}")
        lines.append(f"  Output           : {sched_output}")
        lines.append(f"  Discarded        : {sched_discard}")
        if sched_discard > 0:
            lines.append("  Reasons:")
            for r, count in sorted(sched_reasons.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"    - {r}: {count}")
        lines.append("")

        # Stage 4: Crawl / Fetching
        fetch_decisions = list(tracker.stage4_fetches.values())
        fetch_input = len(fetch_decisions)
        fetch_output = sum(1 for f in fetch_decisions if f["status_code"] == 200)
        fetch_discard = fetch_input - fetch_output

        fetch_reasons = {}
        for f in fetch_decisions:
            if f["status_code"] != 200:
                err = f["error"] or f"HTTP {f['status_code']}"
                fetch_reasons[err] = fetch_reasons.get(err, 0) + 1

        lines.append("Stage 4 - Crawl/Fetching")
        lines.append(f"  Input (Scheduled): {fetch_input}")
        lines.append(f"  Output (Success) : {fetch_output}")
        lines.append(f"  Discarded        : {fetch_discard}")
        if fetch_discard > 0:
            lines.append("  Reasons:")
            for r, count in sorted(fetch_reasons.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"    - {r}: {count}")
        lines.append("")

        # Stage 5: Extraction
        extract_decisions = list(tracker.stage5_extractions.values())
        extract_input = len(extract_decisions)
        extract_output = sum(1 for e in extract_decisions if e["success"])
        extract_discard = extract_input - extract_output

        extract_reasons = {}
        for e in extract_decisions:
            if not e["success"]:
                err = e["error"] or "Extraction Failure"
                extract_reasons[err] = extract_reasons.get(err, 0) + 1

        lines.append("Stage 5 - Job Extraction")
        lines.append(f"  Input            : {extract_input}")
        lines.append(f"  Output (Success) : {extract_output}")
        lines.append(f"  Discarded        : {extract_discard}")
        if extract_discard > 0:
            lines.append("  Reasons:")
            for r, count in sorted(extract_reasons.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"    - {r}: {count}")
        lines.append("")

        # Stage 6 & 7: Deduplication & Filtering (existing decisions)
        filt_decisions = list(tracker.filtering_decisions.values())
        filt_input = len(filt_decisions)
        filt_output = sum(1 for f in filt_decisions if f["accepted"])
        filt_discard = filt_input - filt_output

        filt_reasons = {}
        for f in filt_decisions:
            if not f["accepted"]:
                r = f["reason"] or "Filtered"
                filt_reasons[r] = filt_reasons.get(r, 0) + 1

        lines.append("Stage 6/7 - Deduplication & Filtering (Existing Pipeline)")
        lines.append(f"  Input            : {filt_input}")
        lines.append(f"  Output (Accepted): {filt_output}")
        lines.append(f"  Discarded        : {filt_discard}")
        if filt_discard > 0:
            lines.append("  Reasons:")
            for r, count in sorted(filt_reasons.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"    - {r}: {count}")
        lines.append("")

        # Persistence
        persist_decisions = list(tracker.persistence_decisions.values())
        persist_input = len(persist_decisions)
        persist_new = sum(1 for p in persist_decisions if p["status"] == "new")
        persist_merged = sum(1 for p in persist_decisions if p["status"] == "merged")
        persist_failed = persist_input - persist_new - persist_merged

        lines.append("Database Persistence")
        lines.append(f"  Input (Filtered) : {persist_input}")
        lines.append(f"  Persisted (New)  : {persist_new}")
        lines.append(f"  Persisted (Merge): {persist_merged}")
        lines.append(f"  Failed/Skipped   : {persist_failed}")
        lines.append("")

        # --- PROVIDER CONVERSION REPORT ---
        lines.append("3. Provider Conversion Breakdown")
        lines.append("=" * 80)
        lines.append(f"{'Provider':<20} | {'Discovered':<10} | {'Scheduled':<10} | {'Fetched':<10} | {'Extracted':<10} | {'Persisted':<10} | {'Returned':<10}")
        lines.append("-" * 90)

        # Collect all unique provider names across stages
        all_providers = set()
        all_providers.update(tracker.stage2_candidates.keys())
        for d in tracker.stage3_scheduler.values():
            all_providers.add(d["provider"])
        for f in tracker.stage4_fetches.values():
            all_providers.add(f["provider"])
        for e in tracker.stage5_extractions.values():
            all_providers.add(e["provider"])
        for f in tracker.filtering_decisions.values():
            all_providers.add(f["provider"])
        for p in tracker.persistence_decisions.values():
            all_providers.add(p["provider"])

        provider_rows = []
        for prov in sorted(all_providers):
            disc = len(tracker.stage2_candidates.get(prov, []))
            
            # Scheduled: Stage 3 Decisions where scheduled is True
            sched = sum(1 for url, d in tracker.stage3_scheduler.items() if d["provider"] == prov and d["scheduled"])
            
            # Fetched: Stage 4 Success
            fetch = sum(1 for url, f in tracker.stage4_fetches.items() if f["provider"] == prov and f["status_code"] == 200)
            
            # Extracted: Stage 5 Success
            ext = sum(1 for url, e in tracker.stage5_extractions.items() if e["provider"] == prov and e["success"])
            
            # Persisted: Saved in DB (either new or merged)
            pers = sum(1 for url, p in tracker.persistence_decisions.items() if p["provider"] == prov and p["status"] in ["new", "merged"])
            
            # Returned: Stage 7 Accepted
            ret = sum(1 for url, f in tracker.filtering_decisions.items() if f["provider"] == prov and f["accepted"])

            provider_rows.append((prov, disc, sched, fetch, ext, pers, ret))
            lines.append(f"{prov:<20} | {disc:<10} | {sched:<10} | {fetch:<10} | {ext:<10} | {pers:<10} | {ret:<10}")

        # Summary of skipped/bottlenecked providers
        lines.append("")
        lines.append("Provider Discard Analysis:")
        for prov, disc, sched, fetch, ext, pers, ret in provider_rows:
            if disc > 0 and ret == 0:
                lines.append(f"  • {prov}: lost completely (Discovered: {disc}, Returned: 0)")
                # Find why
                # Was it never scheduled?
                un_sched = [url for url, d in tracker.stage3_scheduler.items() if d["provider"] == prov and not d["scheduled"]]
                if un_sched:
                    reasons = [tracker.stage3_scheduler[u]["reason"] for u in un_sched]
                    lines.append(f"    - Stage 3 Discard: {len(un_sched)} URLs skipped. Reasons: {list(set(reasons))}")
                
                # Fetch failures
                fetch_fails = [url for url, f in tracker.stage4_fetches.items() if f["provider"] == prov and f["status_code"] != 200]
                if fetch_fails:
                    reasons = [tracker.stage4_fetches[u]["error"] or f"HTTP {tracker.stage4_fetches[u]['status_code']}" for u in fetch_fails]
                    lines.append(f"    - Stage 4 Discard: {len(fetch_fails)} HTTP failures. Errors: {list(set(reasons))}")

                # Extraction failures
                ext_fails = [url for url, e in tracker.stage5_extractions.items() if e["provider"] == prov and not e["success"]]
                if ext_fails:
                    reasons = [tracker.stage5_extractions[u]["error"] or "Parsing error" for u in ext_fails]
                    lines.append(f"    - Stage 5 Discard: {len(ext_fails)} Parser failures. Reasons: {list(set(reasons))}")

        lines.append("=" * 80)
        return "\n".join(lines)

    @staticmethod
    def write_reports(tracker: PipelineTracker, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        
        # Text Report
        txt_path = os.path.join(output_dir, "pipeline_report.txt")
        report = PipelineReportGenerator.generate_report(tracker)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"Wrote text report to: {txt_path}")

        # JSON Event stream
        json_path = os.path.join(output_dir, "pipeline_events.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "stage_durations": tracker.stage_durations,
                "total_duration": tracker.total_duration,
                "events": tracker.events
            }, f, indent=2)
        logger.info(f"Wrote JSON events log to: {json_path}")
