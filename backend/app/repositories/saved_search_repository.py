"""
Saved Search Repository

Provides database access queries for SavedSearch objects using SQLAlchemy AsyncSession.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.saved_search import SavedSearch


class SavedSearchRepository:
    """
    Data access layer for SavedSearch entities.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> SavedSearch:
        """
        Creates and persists a new SavedSearch entry.
        """
        saved_search = SavedSearch(
            id=uuid.uuid4(),
            user_id=user_id,
            name=name.strip(),
            query=query.strip() if query else None,
            filters=filters or {},
            created_at=datetime.now(timezone.utc),
            last_run=None
        )
        self.db.add(saved_search)
        await self.db.commit()
        await self.db.refresh(saved_search)
        return saved_search

    async def get_user_searches(self, user_id: uuid.UUID) -> List[SavedSearch]:
        """
        Retrieves all saved search entries for a specific user ordered by created_at desc.
        """
        result = await self.db.execute(
            select(SavedSearch)
            .where(SavedSearch.user_id == user_id)
            .order_by(SavedSearch.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, search_id: uuid.UUID, user_id: uuid.UUID) -> Optional[SavedSearch]:
        """
        Retrieves a single saved search entry by ID for a specific user.
        """
        result = await self.db.execute(
            select(SavedSearch).where(
                and_(SavedSearch.id == search_id, SavedSearch.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, search_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Deletes a saved search entry by ID. Returns True if deleted, False if not found.
        """
        search_entry = await self.get_by_id(search_id, user_id)
        if not search_entry:
            return False

        await self.db.delete(search_entry)
        await self.db.commit()
        return True

    async def update_last_run(self, search_id: uuid.UUID, user_id: uuid.UUID) -> Optional[SavedSearch]:
        """
        Updates last_run timestamp for a saved search entry.
        """
        search_entry = await self.get_by_id(search_id, user_id)
        if not search_entry:
            return None

        search_entry.last_run = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(search_entry)
        return search_entry
