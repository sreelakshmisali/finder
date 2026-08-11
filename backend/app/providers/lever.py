"""
Lever Job Provider

Implements `JobProvider` for Lever ATS public postings API.
Fetches public postings from Lever job boards and transforms them into `NormalizedJob`.
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

# Sample tech companies using Lever
SAMPLE_LEVER_COMPANIES = [
    "netflix", "spotify", "palantir", "twitch",
    "atlassian", "plaid", "dbt", "roblox"
]


class LeverProvider(ATSProvider):
    """
    Job provider for Lever Job Boards.
    """

    @property
    def source_name(self) -> str:
        return "lever"

    @property
    def display_name(self) -> str:
        return "Lever"

    @property
    def description(self) -> str:
        return "Discovers postings from technology companies using Lever ATS."

    async def discover(self, context: DiscoveryContext) -> List[NormalizedJob]:
        """
        Executes discovery on Lever board endpoints matching DiscoveryContext concurrently.
        """
        query = context.query
        results: List[NormalizedJob] = []
        search_kw = (query.query or "").lower()
        search_loc = (query.location or "").lower()

        from app.utils.search_diagnostics import current_diagnostics
        diag = current_diagnostics.get()
        if diag:
            diag.start_provider(self.source_name, self.display_name, priority=20)
            diag.record_provider_stage(self.source_name, p1_searched=len(SAMPLE_LEVER_COMPANIES))

        async def fetch_company(client: httpx.AsyncClient, company: str):
            url = f"https://api.lever.co/v0/postings/{company}?mode=json"
            if diag:
                diag.record_provider_stage(self.source_name, search_url=url)
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return company, resp.json()
            except Exception as exc:
                logger.warning(f"Lever fetch failed for company '{company}': {exc}")
            return company, None

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            company_results = await asyncio.gather(*[fetch_company(client, c) for c in SAMPLE_LEVER_COMPANIES])

        raw_fetched_count = 0
        limit_triggered = False
        # Fair per-company cap: each company can contribute at most this many
        # candidates, so no single company can starve the rest before ranking.
        per_company_cap = max(5, math.ceil(query.limit / max(len(SAMPLE_LEVER_COMPANIES), 1)))

        for company, postings in company_results:
            if not postings or not isinstance(postings, list):
                continue

            raw_fetched_count += len(postings)
            company_name = company.capitalize()
            company_accepted = 0

            for post in postings:
                title = post.get("text", "")
                categories = post.get("categories", {})
                loc = categories.get("location", "Remote")
                job_url = post.get("hostedUrl", "")
                desc_text = post.get("descriptionPlain", "") or post.get("description", "")

                # Filter location
                if search_loc:
                    if search_loc not in loc.lower():
                        if diag:
                            diag.record_provider_stage(self.source_name, p3_rejected=1, rejection_reason="location_mismatch")
                        continue

                # Filter remote
                work_type = post.get("workplaceType", "").lower()
                is_remote = "remote" in loc.lower() or work_type == "remote" or "remote" in title.lower()
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
                        description=desc_text or f"{title} position at {company_name}.",
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
                    location="lever.py:L103",
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
        Fetch full details for a Lever URL.
        """
        return None
