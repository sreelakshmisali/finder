"""
Application Service

Business logic layer managing application lifecycle, state machine transitions,
and audit log generation.

Valid Application Statuses:
- `saved`: Bookmarked role for later review.
- `approved`: User approved for application submission.
- `queued`: Waiting in automation queue.
- `running`: Playwright browser actively filling form.
- `awaiting_input`: Custom questions surfaced for user input.
- `awaiting_confirmation`: Form filled; awaiting user final confirmation submit.
- `completed`: Successfully applied.
- `failed`: Automation failure or user cancellation.
- `interview`: Interview call scheduled.
- `rejected`: Application declined.
- `offer`: Job offer received.
"""

import logging
import uuid
from typing import Optional, Sequence
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdateStatus,
    ApplicationUpdateNotes,
    ApplicationResponse,
    ApplicationListResponse
)
from app.services.matching_service import MatchingService

logger = logging.getLogger(__name__)

VALID_STATUSES = {
    "saved", "approved", "queued", "running",
    "awaiting_input", "awaiting_confirmation",
    "completed", "failed", "interview", "rejected", "offer"
}


class ApplicationService:
    """
    Service layer orchestrating application state transitions and tracking.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ApplicationRepository(db)
        self.job_repo = JobRepository(db)

    async def create_application(self, payload: ApplicationCreate) -> ApplicationResponse:
        """
        Creates a new application record for a job posting.
        Calculates initial match score if available.
        """
        if payload.status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{payload.status}'. Valid statuses: {VALID_STATUSES}"
            )

        # Check job exists
        job = await self.job_repo.get_by_id(payload.job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID '{payload.job_id}' not found."
            )

        # Calculate match score snapshot
        match_score = None
        match_details = None
        try:
            matcher = MatchingService(self.db)
            match_res = await matcher.match_job(payload.job_id)
            match_score = match_res.score
            match_details = match_res.model_dump()
        except Exception as exc:
            logger.warning(f"Could not compute match score for application: {exc}")

        app = await self.repo.create(
            job_id=payload.job_id,
            status=payload.status,
            match_score=match_score,
            match_details=match_details,
            notes=payload.notes
        )

        return ApplicationResponse.model_validate(app)

    async def get_all_applications(self, status_filter: Optional[str] = None) -> ApplicationListResponse:
        """
        Retrieves all applications with optional status filter.
        """
        apps = await self.repo.get_all(status_filter=status_filter)
        responses = [ApplicationResponse.model_validate(a) for a in apps]
        return ApplicationListResponse(total=len(responses), applications=responses)

    async def get_application_by_id(self, application_id: uuid.UUID) -> Optional[ApplicationResponse]:
        """
        Retrieves a single application by ID with audit logs.
        """
        app = await self.repo.get_by_id(application_id)
        if not app:
            return None
        return ApplicationResponse.model_validate(app)

    async def update_status(self, application_id: uuid.UUID, payload: ApplicationUpdateStatus) -> ApplicationResponse:
        """
        Transitions application status and records an audit log entry.
        """
        if payload.status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{payload.status}'. Valid statuses: {VALID_STATUSES}"
            )

        updated_app = await self.repo.update_status(
            application_id=application_id,
            new_status=payload.status,
            details=payload.details
        )

        if not updated_app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' not found."
            )

        return ApplicationResponse.model_validate(updated_app)

    async def update_notes(self, application_id: uuid.UUID, payload: ApplicationUpdateNotes) -> ApplicationResponse:
        """
        Updates user notes for an application.
        """
        updated_app = await self.repo.update_notes(
            application_id=application_id,
            notes=payload.notes
        )

        if not updated_app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' not found."
            )

        return ApplicationResponse.model_validate(updated_app)
