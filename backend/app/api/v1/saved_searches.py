"""
Saved Searches API Endpoints

Provides REST endpoints for saving job search rules, listing saved searches,
executing saved searches, and deleting saved search entries.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.saved_search import SavedSearchCreate, SavedSearchResponse
from app.repositories.saved_search_repository import SavedSearchRepository

router = APIRouter(prefix="/saved-searches", tags=["Saved Searches"])


@router.post(
    "/",
    response_model=SavedSearchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a job search rule",
    description="Saves search query terms and filter criteria for reuse."
)
async def create_saved_search(
    payload: SavedSearchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create saved search endpoint (Authenticated).
    """
    repo = SavedSearchRepository(db)
    return await repo.create(
        user_id=current_user.id,
        name=payload.name,
        query=payload.query,
        filters=payload.filters
    )


@router.get(
    "/",
    response_model=List[SavedSearchResponse],
    summary="List all saved searches",
    description="Retrieves all saved search rules created by the current user."
)
async def list_saved_searches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List saved searches endpoint (Authenticated).
    """
    repo = SavedSearchRepository(db)
    return await repo.get_user_searches(user_id=current_user.id)


@router.post(
    "/{search_id}/run",
    response_model=SavedSearchResponse,
    summary="Execute saved search",
    description="Updates last_run timestamp for the saved search rule."
)
async def execute_saved_search(
    search_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute saved search endpoint (Authenticated).
    """
    repo = SavedSearchRepository(db)
    updated = await repo.update_last_run(search_id=search_id, user_id=current_user.id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved search with ID '{search_id}' not found."
        )
    return updated


@router.delete(
    "/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved search",
    description="Permanently deletes a saved search rule."
)
async def delete_saved_search(
    search_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete saved search endpoint (Authenticated).
    """
    repo = SavedSearchRepository(db)
    deleted = await repo.delete(search_id=search_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved search with ID '{search_id}' not found."
        )
    return None
