from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import admin_event_repository as events
from app.services.source_extraction_service import SourceExtractionService
from app.services.source_importer import SourceImporter
from common.auth.dependencies import CurrentUser, require_admin
from common.db.session import get_db_session

router = APIRouter(prefix="/admin/events", tags=["admin-event-sources"])


@router.post("/{event_id}/sources")
async def import_source(
    event_id: str,
    title: Annotated[str, Form()],
    text_value: Annotated[str | None, Form(alias="text")] = None,
    source_type: Annotated[str, Form()] = "reference",
    publisher: Annotated[str | None, Form()] = None,
    source_url: Annotated[str | None, Form()] = None,
    edition_year: Annotated[int | None, Form()] = None,
    file: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    _ensure_editable(event)
    metadata = {"sourceType": source_type, "publisher": publisher, "sourceUrl": source_url, "editionYear": edition_year}
    try:
        extraction = await SourceExtractionService().extract(file=file, text_value=text_value, metadata=metadata)
        result = await SourceImporter().import_chunks(
            db,
            event_id=event["id"],
            title=title,
            chunks=extraction.chunks,
            metadata=extraction.metadata,
            grade_tags=list(event["grade_tags"] or []),
        )
        await db.commit()
        return result
    except RuntimeError as exc:
        await db.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{event_id}/sources")
async def list_sources(
    event_id: str,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> list[dict]:
    event = await _require_event(db, event_id)
    return await _list_sources(db, event["id"])


@router.delete("/{event_id}/sources/{source_id}")
async def archive_source(
    event_id: str,
    source_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(require_admin),
) -> dict:
    event = await _require_event(db, event_id)
    _ensure_editable(event)
    await db.execute(
        text(
            """
            UPDATE public.rag_source_documents SET status = 'archived'
            WHERE id = :source_id AND source_ref_id = :event_id
            """
        ),
        {"source_id": source_id, "event_id": event["id"]},
    )
    await db.commit()
    return {"id": str(source_id), "status": "archived"}


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
        text(
            """
            SELECT id, title, source_scope, source_ref_type, source_ref_id,
              grade_tags, metadata, status, created_at
            FROM public.rag_source_documents
            WHERE source_ref_type = 'admin_event_source'
              AND source_ref_id = :event_id
              AND status != 'archived'
            ORDER BY created_at DESC
            """
        ),
        {"event_id": event_id},
    )
    return [dict(row) for row in result.mappings().all()]
