from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.workspace.page_manager import PageManager
from common.auth.dependencies import CurrentUser, get_current_user
from common.db.session import get_db_session

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("")
async def list_pages(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sourceMode: str | None = Query(default=None, pattern="^(research|creator)$"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    return await PageManager(db).list_pages(current_user.id, limit=limit, offset=offset, source_mode=sourceMode)


@router.get("/{page_id}")
async def get_page(
    page_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    page = await PageManager(db).get_page(page_id, current_user.id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return page
