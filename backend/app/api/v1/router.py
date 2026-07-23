"""
API V1 Router

Aggregates all version 1 API sub-routers (jobs, dashboard, resume, preferences, applications, auth, health, companies) into a single router.
"""

from fastapi import APIRouter
from app.api.v1.jobs import router as jobs_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.resume import router as resume_router
from app.api.v1.preferences import router as preferences_router
from app.api.v1.applications import router as applications_router
from app.api.v1.auth import router as auth_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.profile import router as profile_router
from app.api.v1.saved_searches import router as saved_searches_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.companies import router as companies_router

api_router = APIRouter()

# Health Check
@api_router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint returning system operational status.
    """
    return {"status": "healthy", "app": "Finder"}

# Sub-routers
api_router.include_router(jobs_router)
api_router.include_router(dashboard_router)
api_router.include_router(resume_router)
api_router.include_router(preferences_router)
api_router.include_router(applications_router)
api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(profile_router)
api_router.include_router(saved_searches_router)
api_router.include_router(notifications_router)
api_router.include_router(companies_router)
