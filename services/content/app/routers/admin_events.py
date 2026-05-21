from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.admin_events import (
    AssetReview,
    AssetSlotUpsert,
    EventCreate,
    EventFactsUpdate,
    EventStatus,
    InteractionsUpdate,
    LessonAssign,
    StoryUpdate,
)
from app.services import admin_asset_repository as assets
from app.services import admin_event_repository as repo
from app.services.story_event_normalizer import normalize_story
from common.auth.dependencies import CurrentUser, require_admin
from common.db.session import get_db_session

router = APIRouter(prefix="/admin/events", tags=["admin-events"])


@router.get("")
async def list_events(
    status_filter: EventStatus | None = None,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> list[dict]:
    return await repo.list_admin_events(db, status_filter)

@router.get("/options")
async def get_options(
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    return await repo.list_admin_options(db)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    try:
        row = await repo.create_event(db, payload.model_dump())
        await db.commit()
        return row
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Event slug or id already exists") from exc
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Cannot create event draft") from exc

@router.post("/{event_id}/revision-draft", status_code=status.HTTP_201_CREATED)
async def create_revision_draft(
    event_id: str,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    try:
        row = await repo.create_revision_draft(db, event_id)
        await db.commit()
        return row
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    story = await repo.get_latest_story(db, event["id"])
    lesson = await repo.get_event_lesson(db, event["id"])
    return {
        "event": event,
        "story": story,
        "assets": await assets.list_asset_slots(db, event["id"]),
        "lesson": lesson,
    }


@router.patch("/{event_id}/facts")
async def update_facts(
    event_id: str,
    payload: EventFactsUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    try:
        row = await repo.update_facts(db, event["id"], payload.model_dump(exclude_unset=True))
        await db.commit()
        return row
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{event_id}/story")
async def update_story(
    event_id: str,
    payload: StoryUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    try:
        story = normalize_story(payload.story, event["title"], event["template_type"])
        row = await repo.upsert_story(db, event["id"], story, payload.generation_metadata)
        await db.commit()
        return row
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{event_id}/interactions")
async def update_interactions(
    event_id: str,
    payload: InteractionsUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    data = {
        "characters": payload.characters,
        "timeline": payload.timeline,
        "climaxScene": payload.climax_scene,
        "aftermath": payload.aftermath,
        "takeaway": payload.takeaway,
        "quiz": payload.quiz,
    }
    try:
        row = await repo.update_interactions(db, event["id"], data)
        await db.commit()
        return row
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{event_id}/assets")
async def upsert_asset_slot(
    event_id: str,
    payload: AssetSlotUpsert,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    try:
        row = await assets.upsert_asset_slot(db, event["id"], payload.model_dump())
        await db.commit()
        return row
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{event_id}/assets/{slot_id}/review")
async def review_asset_slot(
    event_id: str,
    slot_id: UUID,
    payload: AssetReview,
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    try:
        row = await assets.review_asset_slot(
            db, slot_id, event["id"], payload.status, payload.review_notes, current_user.id
        )
        await db.commit()
        return row
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{event_id}/lesson")
async def assign_lesson(
    event_id: str,
    payload: LessonAssign,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    try:
        result = await repo.assign_event_lesson(db, event["id"], payload.lesson_id)
        await db.commit()
        return {"lesson": result}
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


async def _require_event(db: AsyncSession, event_id: str) -> dict:
    event = await repo.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
