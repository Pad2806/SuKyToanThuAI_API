"""Content Service config."""
from shared.config import BaseConfig


class Config(BaseConfig):
    DATABASE_URL: str = ""
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    SERVICE_TOKEN: str = "change-me-internal-service-token"
    STORY_SERVICE_URL: str = "http://story-service:8004"
    RAG_SERVICE_URL: str = "http://rag-service:8003"


config = Config()
