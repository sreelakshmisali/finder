"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1.router import api_router
from app.database.session import init_db
from app.utils.logging import setup_logging

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown tasks."""
    setup_logging()
    # Initialize DB tables for development (in production, use Alembic)
    await init_db()
    yield
    # Clean up resources on shutdown if needed

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered Job Application Assistant API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware setup - Allow all origins for dev flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include main router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/", summary="Root endpoint")
async def root():
    """Root endpoint returning basic app info."""
    return {
        "app": settings.APP_NAME,
        "version": app.version,
        "docs_url": "/docs"
    }
