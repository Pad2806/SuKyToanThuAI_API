from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.mappers import grade_from_row
from common.db.session import get_db_session

router = APIRouter(prefix="/grades", tags=["grades"])


@router.get("")
async def list_grades(db: AsyncSession = Depends(get_db_session)) -> list[dict]:
    result = await db.execute(text("SELECT * FROM public.grades ORDER BY order_index ASC"))
    return [grade_from_row(row) for row in result.mappings().all()]

