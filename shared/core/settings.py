"""Shared base settings inherited by each microservice.

Each service's own settings.py extends BaseServiceSettings and
adds only the env vars it needs.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Every service needs these
    DATABASE_URL: str
    APP_ENV: str = "development"
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    API_PREFIX: str = "/api/v1"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


# Concrete instance used by shared modules (services override this)
class Settings(BaseServiceSettings):
    pass


settings = Settings()
