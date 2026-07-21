"""
Database Connection Management

Handles async SQLAlchemy engine creation, session management, and table creation.
PostgreSQL-only — the application will fail fast with a clear error if PostgreSQL
is unreachable.
"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import get_settings
from app.database.base import Base

logger = logging.getLogger(__name__)
settings = get_settings()

_engine = None
_sessionmaker = None


def get_engine():
    """Returns current active engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            future=True,
            pool_pre_ping=True,
        )
    return _engine


def get_sessionmaker():
    """Returns current active sessionmaker."""
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _sessionmaker


async def init_db():
    """
    Initialize database connection and create tables.

    PostgreSQL-only — raises immediately if the connection fails.
    No SQLite fallback.
    """
    engine = get_engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully with PostgreSQL.")
    except Exception as exc:
        logger.critical(
            f"FATAL: Cannot connect to PostgreSQL database. "
            f"Ensure PostgreSQL is running and DATABASE_URL is correct. "
            f"Error: {exc}"
        )
        raise SystemExit(
            f"FATAL: PostgreSQL connection failed — {exc}. "
            f"Run 'docker compose -f docker/docker-compose.yml up -d' to start the database."
        ) from exc
