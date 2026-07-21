"""
Application Repository

Database access layer for Application and ApplicationLog entities.
"""

import logging
import uuid
from typing import List, Optional, Sequence
from datetime import datetime
from sqlalchemy import select, update, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationLog

logger = logging.getLogger(__name__)


class ApplicationRepository:
    """
    DAO for managing Application records and log history.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, application_id: uuid.UUID) -> Optional[Application]:
        """
        Fetch single application by UUID with joined job and logs.
        """
        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(joinedload(Application.job), joinedload(Application.logs))
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_job_id(self, job_id: uuid.UUID) -> Optional[Application]:
        """
        Fetch application for a given job ID.
        """
        stmt = select(Application).where(Application.job_id == job_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(
        self,
        job_id: uuid.UUID,
        status: str = "saved",
        match_score: Optional[float] = None,
        match_details: Optional[dict] = None,
        notes: Optional[str] = None
    ) -> Application:
        """
        Creates a new Application record and writes an initial audit log entry.
        """
        # Check if an application already exists for this job
        existing = await self.get_by_job_id(job_id)
        if existing:
            return existing

        app = Application(
            job_id=job_id,
            status=status,
            match_score=match_score,
            match_details=match_details,
            notes=notes
        )
        self.db.add(app)
        await self.db.flush()

        # Create initial audit log entry
        log_entry = ApplicationLog(
            application_id=app.id,
            action="Application Created",
            old_status=None,
            new_status=status,
            details=f"Application created with status '{status}'."
        )
        self.db.add(log_entry)

        await self.db.commit()
        return await self.get_by_id(app.id)  # Re-fetch with joined relationships

    async def update_status(
        self,
        application_id: uuid.UUID,
        new_status: str,
        details: Optional[str] = None
    ) -> Optional[Application]:
        """
        Updates status and appends an audit log entry.
        """
        app = await self.get_by_id(application_id)
        if not app:
            return None

        old_status = app.status
        app.status = new_status

        if new_status == "completed" and not app.applied_date:
            app.applied_date = datetime.utcnow()

        log_entry = ApplicationLog(
            application_id=app.id,
            action=f"Status Changed to '{new_status}'",
            old_status=old_status,
            new_status=new_status,
            details=details or f"Transitioned status from '{old_status}' to '{new_status}'."
        )
        self.db.add(log_entry)

        await self.db.commit()
        return await self.get_by_id(app.id)

    async def update_notes(self, application_id: uuid.UUID, notes: str) -> Optional[Application]:
        """
        Updates user notes on an application.
        """
        app = await self.get_by_id(application_id)
        if not app:
            return None

        app.notes = notes
        await self.db.commit()
        return await self.get_by_id(app.id)

    async def get_all(
        self,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Sequence[Application]:
        """
        Queries all applications filtered by status or search keyword.
        """
        stmt = (
            select(Application)
            .options(joinedload(Application.job), joinedload(Application.logs))
            .order_by(Application.updated_at.desc())
        )

        if status_filter and status_filter.lower() != "all":
            stmt = stmt.where(Application.status == status_filter.lower())

        result = await self.db.execute(stmt)
        return result.unique().scalars().all()
