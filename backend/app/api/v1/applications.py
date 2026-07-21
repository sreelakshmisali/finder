"""
Applications API Endpoints

Provides HTTP REST routes for tracking application lifecycles and triggering Playwright form automation.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdateStatus,
    ApplicationUpdateNotes,
    ApplicationResponse,
    ApplicationListResponse
)
from app.schemas.automation import (
    AutomationStartRequest,
    AutomationStateResponse,
    AutomationConfirmSubmitRequest
)
from app.services.application_service import ApplicationService
from app.services.automation_service import AutomationService

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or save application",
    description="Bookmarks a job or approves it for application."
)
async def create_application(
    payload: ApplicationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create application endpoint.
    """
    service = ApplicationService(db)
    return await service.create_application(payload)


@router.get(
    "/",
    response_model=ApplicationListResponse,
    summary="List tracked applications",
    description="Retrieves all tracked applications with optional status filtering."
)
async def list_applications(
    status: Optional[str] = Query(None, description="Status filter (e.g. 'saved', 'approved', 'interview')"),
    db: AsyncSession = Depends(get_db)
):
    """
    List applications endpoint.
    """
    service = ApplicationService(db)
    return await service.get_all_applications(status_filter=status)


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Get single application details",
    description="Retrieves full details and audit logs for an application."
)
async def get_application(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Get application endpoint.
    """
    service = ApplicationService(db)
    app = await service.get_application_by_id(application_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID '{application_id}' not found."
        )
    return app


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse,
    summary="Update application status",
    description="Transitions an application's status and appends an audit log entry."
)
async def update_application_status(
    application_id: uuid.UUID,
    payload: ApplicationUpdateStatus,
    db: AsyncSession = Depends(get_db)
):
    """
    Update status endpoint.
    """
    service = ApplicationService(db)
    return await service.update_status(application_id, payload)


@router.patch(
    "/{application_id}/notes",
    response_model=ApplicationResponse,
    summary="Update application notes",
    description="Updates user notes for an application."
)
async def update_application_notes(
    application_id: uuid.UUID,
    payload: ApplicationUpdateNotes,
    db: AsyncSession = Depends(get_db)
):
    """
    Update notes endpoint.
    """
    service = ApplicationService(db)
    return await service.update_notes(application_id, payload)


@router.post(
    "/{application_id}/start-automation",
    response_model=AutomationStateResponse,
    summary="Start Playwright form filling automation",
    description="Navigates to job application page, fills candidate info, attaches PDF resume, and pauses for user confirmation."
)
async def start_automation(
    application_id: uuid.UUID,
    payload: Optional[AutomationStartRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Start automation endpoint.
    """
    auto_service = AutomationService(db)
    answers = payload.answers if payload else None
    return await auto_service.start_automation(application_id, answers=answers)


@router.post(
    "/{application_id}/confirm-submit",
    response_model=ApplicationResponse,
    summary="Confirm and submit application",
    description="Executes final application submission after explicit user confirmation."
)
async def confirm_submit(
    application_id: uuid.UUID,
    payload: AutomationConfirmSubmitRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm and submit endpoint.
    """
    auto_service = AutomationService(db)
    return await auto_service.confirm_and_submit(application_id, payload)
