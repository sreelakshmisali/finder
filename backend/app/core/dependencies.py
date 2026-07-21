"""Dependencies for FastAPI routes."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_sessionmaker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that yields a database session using the active sessionmaker.
    """
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        yield session
