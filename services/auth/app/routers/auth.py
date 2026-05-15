from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from common.auth.jwt_handler import create_access_token, create_refresh_token, verify_token
from common.auth.password import hash_password, verify_password
from common.db.session import get_db_session
from common.redis.client import blacklist_token, is_token_blacklisted

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    profile = Profile(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name or payload.email.split("@")[0],
    )
    db.add(profile)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered") from exc
    await db.refresh(profile)
    return _tokens_for(profile)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    profile = await _get_by_email(db, payload.email.lower())
    if profile is None or not verify_password(payload.password, profile.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _tokens_for(profile)


@router.post("/refresh")
async def refresh(payload: dict[str, str]) -> dict[str, str]:
    refresh_token = payload.get("refresh_token", "")
    token_payload = verify_token(refresh_token, expected_type="refresh")
    if token_payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if await is_token_blacklisted(str(token_payload["jti"])):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")
    access_token = create_access_token(str(token_payload["sub"]), str(token_payload.get("role", "user")))
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(payload: dict[str, str]) -> dict[str, str]:
    refresh_token = payload.get("refresh_token", "")
    token_payload = verify_token(refresh_token, expected_type="refresh")
    if token_payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    expires_at = int(token_payload["exp"])
    ttl_seconds = max(1, expires_at - int(datetime.now(UTC).timestamp()))
    await blacklist_token(str(token_payload["jti"]), ttl_seconds)
    return {"status": "ok"}


async def _get_by_email(db: AsyncSession, email: str) -> Profile | None:
    result = await db.execute(select(Profile).where(Profile.email == email))
    return result.scalar_one_or_none()


def _tokens_for(profile: Profile) -> TokenResponse:
    subject = str(profile.id)
    return TokenResponse(
        access_token=create_access_token(subject, profile.role),
        refresh_token=create_refresh_token(subject, profile.role),
    )

