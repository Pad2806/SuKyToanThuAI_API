from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.generation.orchestrator import GenerationOrchestrator
from app.schemas.creator import CreatorRequest
from common.auth.dependencies import CurrentUser, get_current_user
from common.db.session import get_db_session

router = APIRouter(tags=["creator"])


@router.post("/create")
async def create(
    payload: CreatorRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    return await GenerationOrchestrator(db).create(
        content=payload.content,
        template=payload.template,
        user_id=current_user.id,
    )

@router.post("/create/{page_id}/confirm-missing")
async def confirm_missing(
    page_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    return await GenerationOrchestrator(db).confirm_missing(page_id, current_user.id)
