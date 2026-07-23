"""
Job Notification Pipeline Service

Implements the candidate job notification pipeline:
1. Run saved search rules (or active resume queries).
2. Fetch live job postings from ATS providers.
3. Run 70/30 Resume-Primary hybrid matching engine.
4. Filter high-fit score postings (>= 80% fit).
5. Create in-app Notifications for candidate alerts.
"""

import logging
import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.job import JobSearchQuery
from app.schemas.notification import PipelineRunResponse
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.repositories.saved_search_repository import SavedSearchRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.resume_repository import ResumeRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Orchestrates the job notification pipeline for candidate users.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.job_service = JobService(db)
        self.matching_service = MatchingService(db)
        self.saved_search_repo = SavedSearchRepository(db)
        self.notification_repo = NotificationRepository(db)
        self.resume_repo = ResumeRepository(db)

    async def run_pipeline(self, user_id: uuid.UUID, min_match_score: float = 75.0) -> PipelineRunResponse:
        """
        Executes the job notification pipeline for a candidate user.
        """
        active_resume = await self.resume_repo.get_active(user_id)
        if not active_resume:
            return PipelineRunResponse(
                user_id=user_id,
                saved_searches_processed=0,
                jobs_evaluated=0,
                new_notifications_created=0,
                message="Pipeline skipped: Active resume is required for job matching alerts."
            )

        saved_searches = await self.saved_search_repo.get_user_searches(user_id)
        searches_to_run: List[JobSearchQuery] = []

        if saved_searches:
            for s in saved_searches:
                f = s.filters or {}
                query_obj = JobSearchQuery(
                    query=s.query,
                    location=f.get("location"),
                    remote_only=bool(f.get("remote_only")),
                    providers=f.get("sources"),
                    min_salary=f.get("min_salary"),
                    manual_search=True,
                    limit=30
                )
                searches_to_run.append(query_obj)
                # Update last_run on saved search
                await self.saved_search_repo.update_last_run(s.id, user_id)
        else:
            # Fallback: run default candidate-aware search query
            searches_to_run.append(
                JobSearchQuery(
                    manual_search=False,
                    limit=30
                )
            )

        jobs_evaluated_count = 0
        new_notifications_count = 0

        for search_query in searches_to_run:
            try:
                search_response = await self.job_service.search_jobs(search_query, user_id=user_id)
                discovered_jobs = search_response.jobs or []

                for job in discovered_jobs:
                    jobs_evaluated_count += 1
                    try:
                        # 3. Match resume against job
                        match_result = await self.matching_service.match_job(job.id, user_id)

                        # 4. Filter high scores (>= 75%)
                        if match_result.score >= min_match_score:
                            # 5. Check if notification already exists
                            already_notified = await self.notification_repo.notification_exists(user_id, job.id)
                            if not already_notified:
                                title = f"⚡ High Match ({Math.round if hasattr(match_result, 'score') else int}({match_result.score})%): {job.title}"
                                message = f"{job.company} • {job.location}. {match_result.reason or 'Strong resume skill fit.'}"

                                await self.notification_repo.create_notification(
                                    user_id=user_id,
                                    job_id=job.id,
                                    notification_type="high_match_job",
                                    title=f"⚡ High Match ({round(match_result.score)}%): {job.title}",
                                    message=f"{job.company} in {job.location}. {match_result.reason or 'Strong alignment with candidate skills.'}"
                                )
                                new_notifications_count += 1
                    except Exception as match_err:
                        logger.warning(f"Error evaluating match for job '{job.id}': {match_err}")

            except Exception as search_err:
                logger.error(f"Error running search query during notification pipeline: {search_err}")

        return PipelineRunResponse(
            user_id=user_id,
            saved_searches_processed=len(searches_to_run),
            jobs_evaluated=jobs_evaluated_count,
            new_notifications_created=new_notifications_count,
            message=f"Pipeline completed: {new_notifications_count} new high-match alerts created from {jobs_evaluated_count} evaluated postings."
        )
