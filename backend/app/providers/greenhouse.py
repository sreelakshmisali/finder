"""
Greenhouse Job Provider

Implements `JobProvider` for Greenhouse ATS public board endpoints.
Queries public Greenhouse board endpoints for companies and maps results to `NormalizedJob`.
"""

import logging
from typing import List, Optional
from datetime import datetime
import httpx

from app.providers.base import JobProvider
from app.schemas.job import JobSearchQuery, NormalizedJob

logger = logging.getLogger(__name__)

# Sample popular tech boards for public search demonstration
SAMPLE_BOARDS = [
    "stripe", "github", "cloudflare", "figma", "airbnb",
    "hashicorp", "datadog", "discord", "canva", "elastic"
]


class GreenhouseProvider(JobProvider):
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

    async def search(self, query: JobSearchQuery) -> List[NormalizedJob]:
        """
        Queries Greenhouse board endpoints concurrently and returns matching normalized jobs.
        """
        results: List[NormalizedJob] = []
        search_kw = (query.query or "").lower()
        search_loc = (query.location or "").lower()

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            for board in SAMPLE_BOARDS:
                try:
                    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
                    resp = await client.get(url)

                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    company_name = board.capitalize()
                    jobs_list = data.get("jobs", [])

                    for item in jobs_list:
                        title = item.get("title", "")
                        loc = item.get("location", {}).get("name", "Remote")
                        job_url = item.get("absolute_url", "")
                        content = item.get("content", "")

                        # Filter by keyword if provided
                        if search_kw:
                            if search_kw not in title.lower() and search_kw not in content.lower():
                                continue

                        # Filter by location if provided
                        if search_loc:
                            if search_loc not in loc.lower():
                                continue

                        # Filter remote if requested
                        is_remote = "remote" in loc.lower() or "remote" in title.lower()
                        if query.remote_only and not is_remote:
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
                                posted_date=datetime.utcnow()
                            )
                        )

                        if len(results) >= query.limit:
                            break

                except Exception as exc:
                    logger.warning(f"Greenhouse fetch failed for board '{board}': {exc}")
                    continue

                if len(results) >= query.limit:
                    break

        return results

    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        """
        Fetch details for a specific Greenhouse job posting URL.
        """
        # Parse job ID and board token from URL if needed
        return None
