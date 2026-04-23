from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str | None = None
    supabase_url: str | None = None

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.supabase_url:
            return self.supabase_url
        raise ValueError("Missing DATABASE_URL or SUPABASE_URL in environment.")


settings = Settings()
