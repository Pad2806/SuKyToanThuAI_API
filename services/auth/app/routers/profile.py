from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.schemas.auth import ProfileResponse, ProfileUpdateRequest
from common.auth.dependencies import CurrentUser, get_current_user
from common.db.session import get_db_session

router = APIRouter(tags=["profile"])


@router.get("/me", response_model=ProfileResponse)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Profile:
    return await _get_profile(db, current_user)


@router.patch("/me", response_model=ProfileResponse)
async def update_me(
    payload: ProfileUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Profile:
    profile = await _get_profile(db, current_user)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile


async def _get_profile(db: AsyncSession, current_user: CurrentUser) -> Profile:
    profile = await db.get(Profile, current_user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

