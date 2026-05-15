from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.mappers import event_from_row
from common.db.session import get_db_session

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search_events(
    q: str = "",
    era: str | None = None,
    grade: str | None = None,
    type: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    clauses = ["status = 'published'", "deleted_at IS NULL"]
    params: dict = {"term": f"%{q.strip()}%", "limit": limit}
    if q.strip():
        clauses.append(
            """
            (
              title ILIKE :term OR summary ILIKE :term OR excerpt ILIKE :term
              OR COALESCE(location, '') ILIKE :term
              OR COALESCE(array_to_string(actors, ' '), '') ILIKE :term
            )
            """
        )
    if era:
        clauses.append("(era_slug = :era OR era_id = :era)")
        params["era"] = era
    if grade:
        clauses.append(":grade = ANY(grade_tags)")
        params["grade"] = grade.upper()
    if type:
        clauses.append("type = :event_type")
        params["event_type"] = type
    result = await db.execute(
        text(
            f"""
            SELECT * FROM public.events
            WHERE {' AND '.join(clauses)}
            ORDER BY year ASC, title ASC
            LIMIT :limit
            """
        ),
        params,
    )
    return [event_from_row(row) for row in result.mappings().all()]

