from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.events import _event_detail
from app.routers.mappers import event_from_row
from common.db.session import get_db_session

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/events/{slug}")
async def internal_event(slug: str, db: AsyncSession = Depends(get_db_session)) -> dict:
    row = await _event_detail(slug, db)
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event_from_row(row, include_story=True)

