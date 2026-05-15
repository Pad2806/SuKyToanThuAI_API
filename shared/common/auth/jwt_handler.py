from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt

from common.config.settings import get_settings


def _create_token(subject: str, role: str, token_type: str, expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "jti": str(uuid4()),
        "type": token_type,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, role: str = "user") -> str:
    settings = get_settings()
    return _create_token(
        subject,
        role,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str, role: str = "user") -> str:
    settings = get_settings()
    return _create_token(
        subject,
        role,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )


def verify_token(token: str, expected_type: str | None = None) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None

    if expected_type and payload.get("type") != expected_type:
        return None
    if not payload.get("sub") or not payload.get("jti"):
        return None
    return payload

