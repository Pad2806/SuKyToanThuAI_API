from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    )
    database_pool_size: int = 2
    database_max_overflow: int = 0
    database_pool_timeout: int = 10
    database_pool_recycle_seconds: int = 1800
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    redis_url: str = "redis://redis:6379/0"
    # Groq (keyword extraction — free)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Google AI
    google_api_key: str = ""
    google_project_id: str = ""
    google_location: str = "us-central1"
    gemini_model: str = "gemini-2.5-flash"
    vertex_gemini_model: str = "gemini-2.5-flash"
    imagen_model: str = "imagen-3.0-generate-001"
    imagen_backup_models: str = ""
    image_backup_provider: str = "gemini,gemini_studio"
    gemini_image_model: str = "gemini-2.5-flash-image"
    gemini_image_location: str = "global"
    # Google AI Studio (separate quota pool from Vertex AI)
    gemini_studio_api_key: str = ""
    gemini_studio_image_model: str = "gemini-2.5-flash-preview-05-20"

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://") and "+asyncpg" not in value:
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
