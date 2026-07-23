"""
Notifications API Endpoints

Provides HTTP REST endpoints for retrieving in-app notifications, fetching unread counts,
marking notifications as read, triggering the Job Notification Pipeline, and deleting alerts.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationUnreadCountResponse,
    PipelineRunResponse,
)
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/",
    response_model=List[NotificationResponse],
    summary="List in-app notifications",
    description="Retrieves candidate in-app notifications and job match alerts."
)
async def list_notifications(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List notifications endpoint (Authenticated).
    """
    repo = NotificationRepository(db)
    return await repo.get_user_notifications(user_id=current_user.id, limit=limit)


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountResponse,
    summary="Get unread notification count",
    description="Returns the total number of unread in-app notifications for badge counter."
)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get unread notification count endpoint (Authenticated).
    """
    repo = NotificationRepository(db)
    count = await repo.get_unread_count(user_id=current_user.id)
    return NotificationUnreadCountResponse(unread_count=count)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark notification as read",
    description="Marks a specific notification entry as read."
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark notification read endpoint (Authenticated).
    """
    repo = NotificationRepository(db)
    updated = await repo.mark_as_read(notification_id=notification_id, user_id=current_user.id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID '{notification_id}' not found."
        )
    return updated


@router.post(
    "/read-all",
    summary="Mark all notifications as read",
    description="Marks all candidate notifications as read."
)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark all notifications read endpoint (Authenticated).
    """
    repo = NotificationRepository(db)
    updated_count = await repo.mark_all_as_read(user_id=current_user.id)
    return {"updated_count": updated_count, "message": "All notifications marked as read."}


@router.post(
    "/run-pipeline",
    response_model=PipelineRunResponse,
    summary="Run job notification pipeline",
    description="Executes saved searches, matches postings against resume, and generates new high-match job alerts."
)
async def trigger_notification_pipeline(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger notification pipeline endpoint (Authenticated).
    """
    service = NotificationService(db)
    return await service.run_pipeline(user_id=current_user.id)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete notification",
    description="Permanently deletes an in-app notification."
)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete notification endpoint (Authenticated).
    """
    repo = NotificationRepository(db)
    deleted = await repo.delete_notification(notification_id=notification_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID '{notification_id}' not found."
        )
    return None
