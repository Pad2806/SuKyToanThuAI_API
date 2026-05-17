from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.events import find_events
from app.routers.mappers import era_from_row
from common.db.session import get_db_session

router = APIRouter(prefix="/eras", tags=["eras"])


@router.get("")
async def list_eras(db: AsyncSession = Depends(get_db_session)) -> list[dict]:
    result = await db.execute(text("SELECT * FROM public.eras ORDER BY order_index ASC"))
    return [era_from_row(row) for row in result.mappings().all()]


@router.get("/{slug}")
async def get_era(slug: str, db: AsyncSession = Depends(get_db_session)) -> dict:
    result = await db.execute(
        text("SELECT * FROM public.eras WHERE slug = :slug OR id = :slug LIMIT 1"),
        {"slug": slug},
    )
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Era not found")
    era = era_from_row(row)
    era["events"] = await find_events(db, era=era["slug"])
    return era
