"""
Dashboard Service

Business logic service for aggregating candidate dashboard statistics:
Queries global total discovered jobs, candidate application status breakdown, and recent activity.
"""

import logging
import uuid
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.application import Application
from app.schemas.dashboard import DashboardStatsResponse, RecentActivityItem
from app.schemas.job import JobResponse

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service layer providing dashboard analytics and stats per user.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self, user_id: uuid.UUID) -> DashboardStatsResponse:
        """
        Calculates and aggregates dashboard stats from the database for a specific user.

        Returns:
            `DashboardStatsResponse` containing job counts and recent activity items.
        """
        # Count total jobs discovered in global catalog
        total_jobs_query = await self.db.execute(select(func.count(Job.id)))
        total_jobs_count = total_jobs_query.scalar() or 0

        # Count candidate's applications by status category
        saved_query = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(Application.user_id == user_id, Application.status == "saved")
            )
        )
        saved_count = saved_query.scalar() or 0

        applied_query = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(Application.user_id == user_id, Application.status == "completed")
            )
        )
        applied_count = applied_query.scalar() or 0

        interview_query = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(Application.user_id == user_id, Application.status == "interview")
            )
        )
        interviews_count = interview_query.scalar() or 0

        offer_query = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(Application.user_id == user_id, Application.status == "offer")
            )
        )
        offers_count = offer_query.scalar() or 0

        # Fetch up to 6 most recently discovered jobs globally
        recent_jobs_query = await self.db.execute(
            select(Job).order_by(Job.fetched_at.desc()).limit(6)
        )
        recent_jobs = recent_jobs_query.scalars().all()
        job_responses = [JobResponse.model_validate(j) for j in recent_jobs]

        # Generate recent activity items
        activities: list[RecentActivityItem] = []
        for job in recent_jobs[:4]:
            activities.append(
                RecentActivityItem(
                    id=str(job.id),
                    title="New Job Discovered",
                    description=f"{job.title} at {job.company} ({job.location})",
                    timestamp=job.fetched_at,
                    type="job_discovered"
                )
            )

        return DashboardStatsResponse(
            total_jobs_found=total_jobs_count,
            saved_jobs_count=saved_count,
            applied_count=applied_count,
            interviews_count=interviews_count,
            offers_count=offers_count,
            recent_jobs=job_responses,
            recent_activities=activities
        )
