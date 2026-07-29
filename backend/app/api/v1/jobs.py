"""
Jobs API Endpoints

Provides HTTP REST endpoints for searching jobs, fetching job details,
listing active job discovery providers, and matching jobs against candidate resumes.
"""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.providers.registry import registry
from app.schemas.job import JobSearchQuery, JobListResponse, JobResponse, ProviderInfo, SearchMode
from app.schemas.match import MatchRequest, MatchResult, BatchMatchRequest, BatchMatchResult
from app.services.job_service import JobService
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get(
    "/search",
    response_model=JobListResponse,
    summary="Search jobs across providers",
    description="Executes concurrent searches across registered ATS providers (Greenhouse, Lever, Ashby)."
)
async def search_jobs(
    q: Optional[str] = Query(None, description="Keywords (e.g. 'Software Engineer', 'Python')"),
    location: Optional[str] = Query(None, description="Location (e.g. 'San Francisco', 'Remote')"),
    remote_only: bool = Query(False, description="Filter for remote roles only"),
    sources: Optional[List[str]] = Query(None, description="Provider filter (e.g. ['greenhouse', 'lever'])"),
    search_mode: SearchMode = Query(SearchMode.NORMAL, description="Search mode to use (NORMAL or SMART)"),
    min_salary: Optional[int] = Query(None, description="Minimum salary threshold filter"),
    force_refresh: bool = Query(False, description="Bypass search cache and force fresh provider search"),
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search jobs endpoint (Authenticated).
    """
    query = JobSearchQuery(
        query=q,
        location=location,
        remote_only=remote_only,
        providers=sources,
        search_mode=search_mode,
        min_salary=min_salary,
        force_refresh=force_refresh,
        limit=limit
    )

    service = JobService(db)
    return await service.search_jobs(query, user_id=current_user.id)


@router.get(
    "/suggested-queries",
    response_model=List[str],
    summary="Get resume-generated search queries",
    description="Returns candidate-aware search suggestions based on active resume skills and search preferences."
)
async def get_suggested_queries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Suggested queries endpoint (Authenticated).
    """
    service = JobService(db)
    return await service.generate_suggested_queries(user_id=current_user.id)



@router.get(
    "/providers",
    response_model=List[ProviderInfo],
    summary="List available job search providers",
    description="Returns metadata for all registered job discovery engines."
)
async def list_providers(current_user: User = Depends(get_current_user)):
    """
    List providers endpoint (Authenticated).
    """
    return registry.list_providers_info()


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get single job details",
    description="Retrieves a specific job posting by its unique ID."
)
async def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get job details endpoint (Authenticated).
    """
    service = JobService(db)
    job = await service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )
    return job


@router.post(
    "/match",
    response_model=MatchResult,
    summary="Match single job with active resume",
    description="Calculates hybrid skill & preference match score and generates AI explanation."
)
async def match_job(
    payload: MatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Match single job endpoint (Authenticated).
    """
    matcher = MatchingService(db)
    try:
        return await matcher.match_job(
            job_id=payload.job_id,
            user_id=current_user.id,
            resume_id=payload.resume_id
        )
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/batch-match",
    response_model=BatchMatchResult,
    summary="Batch match multiple jobs",
    description="Calculates match scores for a list of job IDs."
)
async def batch_match_jobs(
    payload: BatchMatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Batch match jobs endpoint (Authenticated).
    """
    matcher = MatchingService(db)
    active_resume = await matcher.resume_repo.get_active(current_user.id)
    if not active_resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active resume is required for job matching. Please upload a PDF resume first."
        )

    results = await matcher.batch_match_jobs(
        job_ids=payload.job_ids,
        user_id=current_user.id,
        resume_id=payload.resume_id
    )
    return BatchMatchResult(matches=results)

