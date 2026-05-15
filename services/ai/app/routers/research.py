from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.generation.orchestrator import GenerationOrchestrator
from app.schemas.research import ResearchRequest
from common.auth.dependencies import CurrentUser, get_current_user
from common.db.session import get_db_session

router = APIRouter(tags=["research"])


@router.post("/research")
async def research(
    payload: ResearchRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    return await GenerationOrchestrator(db).research(
        query=payload.query,
        template=payload.template,
        user_id=current_user.id,
    )

