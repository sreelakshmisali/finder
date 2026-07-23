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
    # Initialize DB tables for development
    await init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered Job Application Assistant API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware setup using configured origins
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
