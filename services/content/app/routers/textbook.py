from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.mappers import grade_from_row
from common.db.session import get_db_session

router = APIRouter(prefix="/textbook", tags=["textbook"])


@router.get("/{grade_slug}")
async def get_textbook(grade_slug: str, db: AsyncSession = Depends(get_db_session)) -> dict:
    grade_result = await db.execute(
        text("SELECT * FROM public.grades WHERE lower(tag) = lower(:slug) OR id = :id LIMIT 1"),
        {"slug": grade_slug, "id": f"grade-{grade_slug.lower()}"},
    )
    grade = grade_result.mappings().first()
    if grade is None:
        raise HTTPException(status_code=404, detail="Grade not found")

    rows = (
        await db.execute(
            text(
                """
                SELECT p.id AS part_id, p.part_number, p.title AS part_title,
                       l.id AS lesson_id, l.lesson_number, l.title AS lesson_title,
                       e.slug AS event_slug
                FROM public.textbook_parts p
                LEFT JOIN public.textbook_lessons l ON l.part_id = p.id
                LEFT JOIN public.events e ON e.id = l.event_id
                WHERE p.grade_id = :grade_id
                ORDER BY p.order_index ASC, l.order_index ASC
                """
            ),
            {"grade_id": grade["id"]},
        )
    ).mappings().all()

    parts: dict[str, dict] = {}
    for row in rows:
        part = parts.setdefault(
            row["part_id"],
            {
                "id": row["part_id"],
                "partNumber": row["part_number"],
                "title": row["part_title"],
                "lessons": [],
            },
        )
        if row["lesson_id"]:
            part["lessons"].append(
                {
                    "id": row["lesson_id"],
                    "lessonNumber": row["lesson_number"],
                    "title": row["lesson_title"],
                    "eventSlug": row["event_slug"],
                }
            )

    return {"grade": grade_from_row(grade), "parts": list(parts.values())}

