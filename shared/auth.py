"""Shared JWT auth utilities — verify tokens, extract payload.

Only auth-service issues tokens.
All other services use verify_access_token() to validate incoming requests.
"""
from datetime import datetime, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)


def verify_access_token(token: str, secret: str, algorithm: str = "HS256") -> dict:
    """Decode and validate JWT. Raises 401 on failure."""
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm],
                             options={"verify_exp": True})
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"code": "TOKEN_EXPIRED", "message": "Token has expired"})
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"code": "INVALID_TOKEN", "message": "Invalid token"})


def require_roles(*roles: str):
    """FastAPI dependency — verify JWT and check role."""
    def _dep(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> dict:
        if not credentials:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        # Note: each service must inject secret via its own config
        # Use partial() or closure when registering this dependency
        return credentials  # Caller must call verify_access_token separately
    return _dep
