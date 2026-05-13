from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # 9router AI Provider
    NINEROUTER_API_KEY: str
    NINEROUTER_BASE_URL: str
    LLM_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"
    IMAGE_MODEL: str = "dall-e-3"

    # S3-compatible Storage
    S3_BUCKET: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_REGION: str = "ap-southeast-1"
    S3_PUBLIC_BASE_URL: str = ""

    # Worker
    WORKER_ID: str = "worker-001"
    WORKER_POLL_INTERVAL_SECONDS: int = 5
    WORKER_JOB_LOCK_TIMEOUT_MINUTES: int = 10

    # App
    APP_ENV: str = "development"
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    API_PREFIX: str = "/api/v1"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
