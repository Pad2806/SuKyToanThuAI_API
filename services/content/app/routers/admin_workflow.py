from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.admin_events import DraftRequest
from app.services import admin_asset_repository as assets
from app.services import admin_event_repository as events
from app.services.admin_draft_generator import AdminDraftGenerator
from app.services.event_asset_slots import required_slots
from app.services.event_publication_service import archive, publish, quality_report, submit_review
from app.services.gcs_asset_store import GcsAssetStore
from app.services.image_prompt_service import build_prompt
from app.services.imagen_client import ImagenClient
from common.auth.dependencies import CurrentUser, require_admin
from common.db.session import get_db_session

router = APIRouter(prefix="/admin/events", tags=["admin-event-workflow"])


@router.post("/{event_id}/ai/draft-story")
async def draft_story(
    event_id: str,
    payload: DraftRequest,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    _ensure_editable(event)
    try:
        return await AdminDraftGenerator().draft_event(
            db, event=event, source_ids=payload.source_ids, query=payload.query
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/{event_id}/quality-check")
async def check_quality(
    event_id: str,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    return await quality_report(db, event["id"], await _list_sources(db, event["id"]))


@router.post("/{event_id}/submit-review")
async def submit_for_review(
    event_id: str,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    _ensure_editable(event)
    try:
        result = await submit_review(db, event["id"], await _list_sources(db, event["id"]))
        await db.commit()
        return result
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{event_id}/publish")
async def publish_event(
    event_id: str,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    try:
        result = await publish(db, event["id"], await _list_sources(db, event["id"]))
        await db.commit()
        return result
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{event_id}/archive")
async def archive_event(
    event_id: str,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    try:
        result = await archive(db, event["id"])
        await db.commit()
        return result
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{event_id}/assets/ensure-slots")
async def ensure_asset_slots(
    event_id: str,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> list[dict]:
    event = await _require_event(db, event_id)
    _ensure_editable(event)
    rows = []
    for slot in required_slots(event.get("template_type")):
        rows.append(await assets.upsert_asset_slot(db, event["id"], slot))
    await db.commit()
    return rows


@router.post("/{event_id}/assets/prompts")
async def generate_asset_prompts(
    event_id: str,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> list[dict]:
    event = await _require_event(db, event_id)
    _ensure_editable(event)
    rows = await assets.list_asset_slots(db, event["id"])
    updates = []
    for slot in rows:
        if slot["status"] == "approved":
            continue
        prompt = build_prompt(event, slot)
        updates.append(await assets.update_asset_slot(db, event["id"], slot["id"], {"prompt": prompt, "status": "prompted"}))
    await db.commit()
    return updates


@router.post("/{event_id}/assets/{slot_id}/generate-image")
async def generate_asset_image(
    event_id: str,
    slot_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    _ensure_editable(event)
    slot = await assets.get_asset_slot(db, event["id"], slot_id)
    if slot is None:
        raise HTTPException(status_code=404, detail="Asset slot not found")
    if slot["status"] == "approved":
        raise HTTPException(status_code=409, detail="Approved assets cannot be regenerated")
    try:
        prompt = slot.get("prompt") or build_prompt(event, slot)
        raw = await ImagenClient().generate_image(prompt)
        stored = GcsAssetStore().save_image(raw, event["id"], slot["slot_key"])
        row = await assets.update_asset_slot(db, event["id"], slot_id, {**stored, "prompt": prompt, "status": "generated"})
        await db.commit()
        return row
    except RuntimeError as exc:
        await assets.update_asset_slot(db, event["id"], slot_id, {"status": "failed", "review_notes": str(exc)})
        await db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        await assets.update_asset_slot(db, event["id"], slot_id, {"status": "rejected", "review_notes": str(exc)})
        await db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


async def _require_event(db: AsyncSession, event_id: str) -> dict:
    event = await events.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

def _ensure_editable(event: dict) -> None:
    if event["status"] not in {"draft", "review"}:
        raise HTTPException(status_code=409, detail="Event is not editable")


async def _list_sources(db: AsyncSession, event_id: str) -> list[dict]:
    result = await db.execute(
        text("SELECT * FROM public.rag_source_documents WHERE source_ref_type = 'admin_event_source' AND source_ref_id = :event_id AND status = 'ready'"),
        {"event_id": event_id},
    )
    return [dict(row) for row in result.mappings().all()]
