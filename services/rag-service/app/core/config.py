"""RAG Service config."""
from shared.config import BaseConfig


class Config(BaseConfig):
    DATABASE_URL: str = ""
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    SERVICE_TOKEN: str = "change-me-internal-service-token"
    NINEROUTER_API_KEY: str = ""
    NINEROUTER_BASE_URL: str = ""
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"
    EMBED_DIM: int = 1024
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = "sukyai"
    PUBLIC_CDN_BASE_URL: str = ""


config = Config()
