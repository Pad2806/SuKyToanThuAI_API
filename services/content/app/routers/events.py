from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.mappers import event_from_row
from common.db.session import get_db_session

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
async def list_events(
    era: str | None = None,
    grade: str | None = None,
    type: str | None = None,
    featured: bool | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    where, params = _filters(era=era, grade=grade, event_type=type, featured=featured)
    params.update({"limit": limit, "offset": offset})
    result = await db.execute(
        text(
            f"""
            SELECT * FROM public.events e
            WHERE {where}
            ORDER BY e.year ASC, e.title ASC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    )
    return [event_from_row(row) for row in result.mappings().all()]


@router.get("/featured")
async def featured_events(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    return await list_events(featured=True, limit=limit, db=db)


@router.get("/{slug}")
async def get_event(slug: str, db: AsyncSession = Depends(get_db_session)) -> dict:
    row = await _event_detail(slug, db)
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event_from_row(row, include_story=True)


@router.get("/{slug}/related")
async def related_events(
    slug: str,
    limit: int = Query(default=3, ge=1, le=20),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    source = await _event_detail(slug, db)
    if source is None:
        raise HTTPException(status_code=404, detail="Event not found")
    result = await db.execute(
        text(
            """
            SELECT * FROM public.events
            WHERE status = 'published' AND deleted_at IS NULL
              AND id != :event_id
              AND (era_id = :era_id OR slug = ANY(:related_slugs))
            ORDER BY year ASC, title ASC
            LIMIT :limit
            """
        ),
        {
            "event_id": source["id"],
            "era_id": source["era_id"],
            "related_slugs": source["related_event_slugs"] or [],
            "limit": limit,
        },
    )
    return [event_from_row(row) for row in result.mappings().all()]


async def _event_detail(slug: str, db: AsyncSession):
    result = await db.execute(
        text(
            """
            SELECT e.*, story.story_json AS story
            FROM public.events e
            LEFT JOIN LATERAL (
              SELECT story_json
              FROM public.event_story_versions
              WHERE event_id = e.id AND status = 'published'
              ORDER BY version_number DESC
              LIMIT 1
            ) story ON true
            WHERE (e.slug = :slug OR e.id = :slug)
              AND e.status = 'published'
              AND e.deleted_at IS NULL
            LIMIT 1
            """
        ),
        {"slug": slug},
    )
    return result.mappings().first()


def _filters(
    era: str | None = None,
    grade: str | None = None,
    event_type: str | None = None,
    featured: bool | None = None,
) -> tuple[str, dict]:
    clauses = ["e.status = 'published'", "e.deleted_at IS NULL"]
    params: dict = {}
    if era:
        clauses.append("(e.era_slug = :era OR e.era_id = :era)")
        params["era"] = era
    if grade:
        clauses.append(":grade = ANY(e.grade_tags)")
        params["grade"] = grade.upper()
    if event_type:
        clauses.append("e.type = :event_type")
        params["event_type"] = event_type
    if featured is not None:
        clauses.append("e.featured = :featured")
        params["featured"] = featured
    return " AND ".join(clauses), params

