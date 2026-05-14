"""Gateway routing table — maps path prefixes to upstream services."""
from app.config import config

ROUTES: list[tuple[str, str]] = [
    ("/api/v1/auth",         config.AUTH_SERVICE_URL),
    ("/api/v1/users",        config.AUTH_SERVICE_URL),
    ("/api/v1/events",       config.CONTENT_SERVICE_URL),
    ("/api/v1/eras",         config.CONTENT_SERVICE_URL),
    ("/api/v1/grades",       config.CONTENT_SERVICE_URL),
    ("/api/v1/lessons",      config.CONTENT_SERVICE_URL),
    ("/api/v1/topics",       config.CONTENT_SERVICE_URL),
    ("/api/v1/documents",    config.RAG_SERVICE_URL),
    ("/api/v1/rag",          config.RAG_SERVICE_URL),
    ("/api/v1/story",        config.STORY_SERVICE_URL),
    ("/api/v1/images",       config.STORY_SERVICE_URL),
    ("/api/v1/review-items", config.STORY_SERVICE_URL),
    ("/api/v1/ai",           config.AI_WORKER_URL),
]


def resolve_upstream(path: str) -> str | None:
    """Find the upstream URL for a given request path."""
    for prefix, upstream in ROUTES:
        if path.startswith(prefix):
            return upstream
    return None
