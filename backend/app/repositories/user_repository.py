"""
User Repository

Database access layer for User entity.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


class UserRepository:
    """
    DAO for managing User accounts in database.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Fetch single user by UUID.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Fetch single user by normalized email address.
        """
        clean_email = email.lower().strip()
        result = await self.db.execute(select(User).where(User.email == clean_email))
        return result.scalar_one_or_none()

    async def create(self, email: str, full_name: str, password: str) -> User:
        """
        Creates a new User record with hashed password.
        """
        hashed_pwd = get_password_hash(password)
        db_user = User(
            email=email.lower().strip(),
            full_name=full_name.strip(),
            password_hash=hashed_pwd,
            is_active=True
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        """
        Updates last_login timestamp for a user.
        """
        await self.db.execute(
            update(User).where(User.id == user_id).values(last_login=datetime.utcnow())
        )
        await self.db.commit()
