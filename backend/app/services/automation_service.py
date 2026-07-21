"""
Automation Service

Orchestrates Playwright form automation for approved applications.

STRICT SAFETY GUARANTEE:
- Finder NEVER automatically submits job applications without user consent.
- `start_automation()` fills standard fields, attaches the PDF resume, and updates status to `awaiting_confirmation`.
- `confirm_and_submit()` is ONLY triggered when the user explicitly clicks 'Confirm & Submit Application' in the UI.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.automation.greenhouse_automator import GreenhouseAutomator
from app.automation.lever_automator import LeverAutomator
from app.automation.ashby_automator import AshbyAutomator
from app.repositories.application_repository import ApplicationRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.automation import AutomationStateResponse, AutomationConfirmSubmitRequest
from app.schemas.application import ApplicationResponse

logger = logging.getLogger(__name__)

AUTOMATOR_MAP = {
    "greenhouse": GreenhouseAutomator(),
    "lever": LeverAutomator(),
    "ashby": AshbyAutomator(),
}


class AutomationService:
    """
    Business logic layer for Playwright job application automation.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.app_repo = ApplicationRepository(db)
        self.resume_repo = ResumeRepository(db)

    def _get_automator(self, source_name: str):
        return AUTOMATOR_MAP.get(source_name.lower(), GreenhouseAutomator())

    async def start_automation(
        self,
        application_id: uuid.UUID,
        answers: Optional[Dict[str, str]] = None
    ) -> AutomationStateResponse:
        """
        Launches Playwright form automation for standard candidate details and resume upload.
        Pauses at `awaiting_confirmation` or `awaiting_input`.
        """
        app = await self.app_repo.get_by_id(application_id)
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' not found."
            )

        # Retrieve active candidate resume
        resume = await self.resume_repo.get_active()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active resume found. Please upload and activate a PDF resume before applying."
            )

        # Prepare candidate info dictionary from parsed resume
        parsed_data = resume.parsed_data or {}
        candidate_info = {
            "full_name": parsed_data.get("full_name", "Applicant Name"),
            "email": parsed_data.get("email", "candidate@example.com"),
            "phone": parsed_data.get("phone", "(555) 019-2834"),
            "skills": parsed_data.get("skills", []),
        }

        # Transition status to 'running'
        await self.app_repo.update_status(
            application_id=app.id,
            new_status="running",
            details="Playwright automation initialized. Navigating to job page."
        )

        automator = self._get_automator(app.job.source)

        # Run form filling automation
        step_result = await automator.fill_form(
            job_url=app.job.url,
            resume_path=resume.file_path,
            candidate_info=candidate_info,
            answers=answers
        )

        # Update application status based on step result
        await self.app_repo.update_status(
            application_id=app.id,
            new_status=step_result.status,
            details=step_result.step_summary
        )

        questions_dict = [q.model_dump() for q in step_result.custom_questions]

        return AutomationStateResponse(
            application_id=app.id,
            status=step_result.status,
            step_summary=step_result.step_summary,
            custom_questions=questions_dict,
            filled_fields_summary=step_result.filled_fields_summary
        )

    async def confirm_and_submit(
        self,
        application_id: uuid.UUID,
        payload: AutomationConfirmSubmitRequest
    ) -> ApplicationResponse:
        """
        Executes final application submission ONLY after explicit user confirmation.
        """
        app = await self.app_repo.get_by_id(application_id)
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' not found."
            )

        resume = await self.resume_repo.get_active()

        candidate_info = {
            "full_name": (resume.parsed_data or {}).get("full_name", "Applicant Name") if resume else "Applicant Name",
            "email": (resume.parsed_data or {}).get("email", "candidate@example.com") if resume else "candidate@example.com",
            "phone": (resume.parsed_data or {}).get("phone", "(555) 019-2834") if resume else "(555) 019-2834",
        }

        automator = self._get_automator(app.job.source)

        # Submit final application
        submit_result = await automator.confirm_and_submit(
            job_url=app.job.url,
            resume_path=resume.file_path if resume else "",
            candidate_info=candidate_info,
            answers=payload.answers or {}
        )

        # Update status to completed
        updated_app = await self.app_repo.update_status(
            application_id=app.id,
            new_status=submit_result.status,
            details=submit_result.step_summary
        )

        return ApplicationResponse.model_validate(updated_app)
