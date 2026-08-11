"""
Ashby Job Provider

Implements `JobProvider` for Ashby HQ public posting API.
Fetches public postings from Ashby job boards and transforms them into `NormalizedJob`.
"""

import asyncio
import logging
import math
from typing import List, Optional
from datetime import datetime
import httpx

from app.providers.base_discovery import ATSProvider, DiscoveryContext
from app.schemas.job import JobSearchQuery, NormalizedJob

logger = logging.getLogger(__name__)

# Sample companies using Ashby
SAMPLE_ASHBY_COMPANIES = [
    "notion", "linear", "ramp", "resend", "vanta", "pinecone", "posthog"
]


class AshbyProvider(ATSProvider):
    """
    Job provider for Ashby HQ Job Boards.
    """

    @property
    def source_name(self) -> str:
        return "ashby"

    @property
    def display_name(self) -> str:
        return "Ashby"

    @property
    def description(self) -> str:
        return "Discovers postings from fast-growing startups and scaleups using Ashby HQ."

    async def discover(self, context: DiscoveryContext) -> List[NormalizedJob]:
        """
        Executes discovery on Ashby board endpoints matching DiscoveryContext concurrently.
        """
        query = context.query
        results: List[NormalizedJob] = []
        search_kw = (query.query or "").lower()
        search_loc = (query.location or "").lower()

        from app.utils.search_diagnostics import current_diagnostics
        diag = current_diagnostics.get()
        if diag:
            diag.start_provider(self.source_name, self.display_name, priority=30)
            diag.record_provider_stage(self.source_name, p1_searched=len(SAMPLE_ASHBY_COMPANIES))

        async def fetch_board(client: httpx.AsyncClient, board: str):
            url = f"https://api.ashbyhq.com/posting-api/job-board/{board}"
            if diag:
                diag.record_provider_stage(self.source_name, search_url=url)
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return board, resp.json()
            except Exception as exc:
                logger.warning(f"Ashby fetch failed for board '{board}': {exc}")
            return board, None

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            board_results = await asyncio.gather(*[fetch_board(client, b) for b in SAMPLE_ASHBY_COMPANIES])

        raw_fetched_count = 0
        limit_triggered = False
        # Fair per-company cap: each company can contribute at most this many
        # candidates, so no single company can starve the rest before ranking.
        per_company_cap = max(5, math.ceil(query.limit / max(len(SAMPLE_ASHBY_COMPANIES), 1)))

        for board, data in board_results:
            if not data or not isinstance(data, dict):
                continue

            company_name = board.capitalize()
            jobs_list = data.get("jobs", [])
            raw_fetched_count += len(jobs_list)
            company_accepted = 0

            for item in jobs_list:
                title = item.get("title", "")
                loc = item.get("locationName", "Remote")
                job_url = item.get("jobUrl", "")
                desc_info = f"{title} position at {company_name} in {loc}."

                # Filter location
                if search_loc:
                    if search_loc not in loc.lower():
                        if diag:
                            diag.record_provider_stage(self.source_name, p3_rejected=1, rejection_reason="location_mismatch")
                        continue

                # Filter remote
                is_remote = item.get("isRemote", False) or "remote" in loc.lower() or "remote" in title.lower()
                if query.remote_only and not is_remote:
                    if diag:
                        diag.record_provider_stage(self.source_name, p3_rejected=1, rejection_reason="remote_only_filter")
                    continue

                results.append(
                    NormalizedJob(
                        company=company_name,
                        title=title,
                        location=loc,
                        remote=is_remote,
                        salary=None,
                        description=desc_info,
                        url=job_url,
                        source=self.source_name,
                        discovery_provider=self.source_name,
                        posted_date=datetime.utcnow()
                    )
                )

                company_accepted += 1
                if company_accepted >= per_company_cap:
                    break  # per-company cap reached; move to next company

            # No outer break — every company is always visited.

        # Trim to global limit after all companies have contributed.
        pre_trim_count = len(results)
        results = results[:query.limit]
        limit_triggered = pre_trim_count > query.limit

        if diag:
            diag.record_provider_stage(
                self.source_name,
                p2_fetched=raw_fetched_count,
                p4_returned=len(results)
            )
            if limit_triggered:
                diag.record_limit_audit(
                    provider=self.source_name,
                    location="ashby.py:L101",
                    variable_name="query.limit",
                    applied_limit=query.limit,
                    input_size=raw_fetched_count,
                    output_size=len(results),
                    effect=f"Provider capped results at query.limit={query.limit} (per_company_cap={per_company_cap})"
                )
            diag.finish_provider(self.source_name, len(results))

        return results

    async def search(self, query: JobSearchQuery) -> List[NormalizedJob]:
        """
        Legacy search method forwarding to discover().
        """
        return await self.discover(DiscoveryContext(query=query))

    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        """
        Fetch full details for an Ashby URL.
        """
        return None
