"""Shared JWT verification middleware.

Each service imports verify_token() to authenticate requests.
Only auth-service issues tokens; all other services just verify.
"""
from datetime import datetime, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer()


def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    secret_key: str,
    algorithm: str = "HS256",
) -> dict:
    """Verify JWT and return payload. Raises 401 if invalid."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            secret_key,
            algorithms=[algorithm],
        )
        if datetime.fromtimestamp(payload["exp"], tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def require_role(*roles: str):
    """FastAPI dependency factory — checks role in JWT payload."""
    def _check(payload: dict = Depends(verify_token)) -> dict:
        if payload.get("role") not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return payload
    return _check


# Standard response envelope
def ok(data, meta: dict | None = None) -> dict:
    return {"data": data, "meta": meta}


def err(code: str, message: str, details=None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}
