"""Auth Service config."""
from shared.config import BaseConfig


class Config(BaseConfig):
    DATABASE_URL: str = ""
    JWT_SECRET: str = "change-me"
    JWT_ISSUER: str = "sukyai"
    JWT_AUDIENCE: str = "sukyai-api"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SERVICE_TOKEN: str = "change-me-internal-service-token"


config = Config()
