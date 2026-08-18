"""Configuration module for the Finder application."""

from functools import lru_cache
from typing import List, Union, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    """Application settings, loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://finder:finder_secret@localhost:5433/finder_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Integrations
    OPENAI_API_KEY: str = ""
    
    # App Settings
    APP_NAME: str = "Finder"
    API_V1_PREFIX: str = "/api/v1"
    UPLOAD_DIR: str = "./uploads"

    # Duplicate Detection Settings
    DEDUP_COMPANY_WEIGHT: float = 0.4
    DEDUP_TITLE_WEIGHT: float = 0.4
    DEDUP_LOCATION_WEIGHT: float = 0.1
    DEDUP_DESCRIPTION_WEIGHT: float = 0.1
    DEDUP_MIN_SCORE_THRESHOLD: float = 0.85
    
    # Search Engine & Ranking Settings
    RANKING_VERSION: str = "v2_intent_engine"
    RANKING_WEIGHT_TITLE: float = 0.60
    RANKING_WEIGHT_SKILLS: float = 0.25
    RANKING_WEIGHT_DESCRIPTION: float = 0.10
    RANKING_WEIGHT_LOCATION: float = 0.05
    
    # Crawl Scheduler Settings (Phase 2)
    CRAWL_BUDGET: int = 60
    MAX_CANDIDATE_PAGES: int = 60
    MAX_CONCURRENT_FETCHES: int = 15
    MAX_JOBS_PER_COMPANY: int = 5
    LINKEDIN_MODE: str = "external_only"
    PROVIDER_OVERRIDES: Optional[str] = None
    SEARCH_DIAGNOSTICS_ENABLED: bool = True

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "http://127.0.0.1"
    ]

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip().rstrip("/") for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(i).strip().rstrip("/") for i in v if str(i).strip()]
        elif isinstance(v, str):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

@lru_cache()
def get_settings() -> Settings:
    """Provides a cached instance of the settings."""
    return Settings()

# Global settings instance singleton
settings = get_settings()
