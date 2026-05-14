"""Gateway config."""
from shared.config import BaseConfig


class Config(BaseConfig):
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    CONTENT_SERVICE_URL: str = "http://content-service:8002"
    RAG_SERVICE_URL: str = "http://rag-service:8003"
    STORY_SERVICE_URL: str = "http://story-service:8004"
    AI_WORKER_URL: str = "http://ai-worker:8005"
    GATEWAY_TIMEOUT: float = 30.0


config = Config()
