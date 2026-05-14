"""AI Worker config."""
from shared.config import BaseConfig


class Config(BaseConfig):
    DATABASE_URL: str = ""
    SERVICE_TOKEN: str = "change-me-internal-service-token"
    NINEROUTER_API_KEY: str = ""
    NINEROUTER_BASE_URL: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"
    IMAGE_MODEL: str = "dall-e-3"
    WORKER_ID: str = "worker-001"
    WORKER_POLL_INTERVAL_SECONDS: int = 5
    WORKER_JOB_LOCK_TIMEOUT_MINUTES: int = 10
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    CONTENT_SERVICE_URL: str = "http://content-service:8002"
    RAG_SERVICE_URL: str = "http://rag-service:8003"
    STORY_SERVICE_URL: str = "http://story-service:8004"
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = "sukyai"


config = Config()
