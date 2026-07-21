"""
Dashboard API Endpoints

Provides HTTP REST endpoint `/dashboard/stats` returning summary statistics and recent activity.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.dashboard import DashboardStatsResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get summary dashboard stats",
    description="Returns aggregate counts for jobs found, application statuses, recent jobs, and activity feed."
)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get dashboard stats endpoint.
    """
    service = DashboardService(db)
    return await service.get_stats()
