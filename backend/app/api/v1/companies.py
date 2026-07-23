"""
Companies API Endpoints

Provides REST endpoints for discovering target companies and career portals.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.company import CompanyDiscoveryResponse, DiscoveredCompany
from app.services.company_discovery_service import CompanyDiscoveryService

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get(
    "/discover",
    response_model=CompanyDiscoveryResponse,
    summary="Discover companies and career portals",
    description="Discovers companies matching technology, location, or industry criteria (e.g. 'Python startups India')."
)
async def discover_companies(
    q: str = Query(..., description="Target search query (e.g. 'Python startups India', 'AI companies careers')"),
    location: Optional[str] = Query(None, description="Optional location filter"),
    technology: Optional[str] = Query(None, description="Optional technology filter"),
    limit: int = Query(10, ge=1, le=50, description="Max companies to return"),
    current_user: User = Depends(get_current_user)
):
    """
    Company discovery endpoint (Authenticated).
    """
    service = CompanyDiscoveryService()
    companies = await service.discover_companies(
        query=q,
        location=location,
        technology=technology,
        limit=limit
    )

    return CompanyDiscoveryResponse(
        total=len(companies),
        companies=companies,
        query_executed=q
    )
