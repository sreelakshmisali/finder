"""Configuration module for the Finder application."""

from functools import lru_cache
from typing import List, Union
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
    

    # CORS
    CORS_ORIGINS: Union[str, List[AnyHttpUrl]] = ["http://localhost:5173"]

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

@lru_cache()
def get_settings() -> Settings:
    """Provides a cached instance of the settings."""
    return Settings()

# Global settings instance singleton
settings = get_settings()
