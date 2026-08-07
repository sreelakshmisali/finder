"""
Greenhouse Job Provider

Implements `JobProvider` for Greenhouse ATS public board endpoints.
Queries public Greenhouse board endpoints for companies and maps results to `NormalizedJob`.
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime
import httpx

from app.providers.base_discovery import ATSProvider, DiscoveryContext
from app.schemas.job import JobSearchQuery, NormalizedJob

logger = logging.getLogger(__name__)

# Sample popular tech boards for public search demonstration
SAMPLE_BOARDS = [
    "stripe", "github", "cloudflare", "figma", "airbnb",
    "hashicorp", "datadog", "discord", "canva", "elastic"
]


class GreenhouseProvider(ATSProvider):
    """
    Job provider for Greenhouse Job Boards.
    """

    @property
    def source_name(self) -> str:
        return "greenhouse"

    @property
    def display_name(self) -> str:
        return "Greenhouse"

    @property
    def description(self) -> str:
        return "Discovers postings from top tech companies using Greenhouse ATS."

    async def discover(self, context: DiscoveryContext) -> List[NormalizedJob]:
        """
        Executes discovery on Greenhouse board endpoints matching DiscoveryContext concurrently.
        """
        query = context.query
        results: List[NormalizedJob] = []
        search_kw = (query.query or "").lower()
        search_loc = (query.location or "").lower()

        from app.utils.search_diagnostics import current_diagnostics
        diag = current_diagnostics.get()
        if diag:
            diag.start_provider(self.source_name, self.display_name, priority=10)
            diag.record_provider_stage(self.source_name, p1_searched=len(SAMPLE_BOARDS))

        async def fetch_board(client: httpx.AsyncClient, board: str):
            url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
            if diag:
                diag.record_provider_stage(self.source_name, search_url=url)
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return board, resp.json()
            except Exception as exc:
                logger.warning(f"Greenhouse fetch failed for board '{board}': {exc}")
            return board, None

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            board_results = await asyncio.gather(*[fetch_board(client, b) for b in SAMPLE_BOARDS])

        raw_fetched_count = 0
        limit_triggered = False

        for board, data in board_results:
            if not data:
                continue

            company_name = board.capitalize()
            jobs_list = data.get("jobs", [])
            raw_fetched_count += len(jobs_list)

            for item in jobs_list:
                title = item.get("title", "")
                loc = item.get("location", {}).get("name", "Remote")
                job_url = item.get("absolute_url", "")
                content = item.get("content", "")

                # Filter by location if provided
                if search_loc:
                    if search_loc not in loc.lower():
                        if diag:
                            diag.record_provider_stage(self.source_name, p3_rejected=1, rejection_reason="location_mismatch")
                        continue

                # Filter remote if requested
                is_remote = "remote" in loc.lower() or "remote" in title.lower()
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
                        description=content or f"{title} position at {company_name}.",
                        url=job_url,
                        source=self.source_name,
                        discovery_provider=self.source_name,
                        posted_date=datetime.utcnow()
                    )
                )

                if len(results) >= query.limit:
                    limit_triggered = True
                    break

            if len(results) >= query.limit:
                limit_triggered = True
                break

        if diag:
            diag.record_provider_stage(
                self.source_name,
                p2_fetched=raw_fetched_count,
                p4_returned=len(results)
            )
            if limit_triggered:
                diag.record_limit_audit(
                    provider=self.source_name,
                    location="greenhouse.py:L102",
                    variable_name="query.limit",
                    applied_limit=query.limit,
                    input_size=raw_fetched_count,
                    output_size=len(results),
                    effect=f"Provider capped results at query.limit={query.limit}"
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
        Fetch details for a specific Greenhouse job posting URL.
        """
        # Parse job ID and board token from URL if needed
        return None
