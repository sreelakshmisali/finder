"""
Dashboard Service

Business logic service for aggregating system statistics:
Queries total discovered jobs, recent job listings, and application status counts.
"""

import logging
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.schemas.dashboard import DashboardStatsResponse, RecentActivityItem
from app.schemas.job import JobResponse

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service layer providing dashboard analytics and stats.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self) -> DashboardStatsResponse:
        """
        Calculates and aggregates dashboard stats from the database.

        Returns:
            `DashboardStatsResponse` containing job counts and recent activity items.
        """
        # Count total jobs discovered in database
        total_jobs_query = await self.db.execute(select(func.count(Job.id)))
        total_jobs_count = total_jobs_query.scalar() or 0

        # Fetch up to 6 most recently discovered jobs
        recent_jobs_query = await self.db.execute(
            select(Job).order_by(Job.fetched_at.desc()).limit(6)
        )
        recent_jobs = recent_jobs_query.scalars().all()
        job_responses = [JobResponse.model_validate(j) for j in recent_jobs]

        # Generate recent activity items from recent jobs
        activities: list[RecentActivityItem] = []
        for job in recent_jobs[:4]:
            activities.append(
                RecentActivityItem(
                    id=str(job.id),
                    title=f"New Job Discovered",
                    description=f"{job.title} at {job.company} ({job.location})",
                    timestamp=job.fetched_at,
                    type="job_discovered"
                )
            )

        # In Step 8 (Application Tracker), applications table counts will populate these
        return DashboardStatsResponse(
            total_jobs_found=total_jobs_count,
            saved_jobs_count=0,
            applied_count=0,
            interviews_count=0,
            offers_count=0,
            recent_jobs=job_responses,
            recent_activities=activities
        )
