import json
import uuid as _uuid


def _safe_uuid(val) -> str | None:
    """Return val as string if it's a valid UUID, else None."""
    if val is None:
        return None
    s = str(val)
    try:
        _uuid.UUID(s)
        return s
    except (ValueError, AttributeError):
        NAMESPACE_SUKY = _uuid.UUID('12345678-1234-5678-1234-567812345678')
        return str(_uuid.uuid5(NAMESPACE_SUKY, s))


def page_summary(row) -> dict:
    payload = row["render_payload"] or {}
    event_data = payload.get("eventData") or {}
    return {
        "id": row["id"],
        "title": row["title"],
        "flowType": row["flow_type"],
        "sourceMode": (row["source_payload"] or {}).get("sourceMode"),
        "template": row["template_key"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "thumbnail": event_data.get("image") or event_data.get("fallbackImage"),
        "coverageSummary": payload.get("coverageReport", {}),
    }


def page_detail(row) -> dict:
    # detail = page_summary(row)
    # detail["renderPayload"] = row["render_payload"] or {}
    from app.generation.story_event_normalizer import normalize_story_event_payload

    detail = page_summary(row)
    payload = row["render_payload"] or {}
    event_data = payload.get("eventData") or {}
    if event_data:
        payload = normalize_story_event_payload(
            payload,
            event_data.get("title") or row["title"],
            row["template_key"] or event_data.get("type") or "universal",
            row["flow_type"],
            (row["source_payload"] or {}).get("sourceMode") or payload.get("sourceMode") or "research",
        )
    detail["renderPayload"] = payload
    return detail


def source_params(page_id, version_id, request_id, source):
    return {
        "page_id": page_id,
        "version_id": version_id,
        "request_id": request_id,
        "source_type": source.get("sourceType", "unknown"),
        "source_id": str(source.get("sourceId") or source.get("chunkId") or "unknown"),
        "source_ref_type": source.get("sourceRefType"),
        "source_ref_id": source.get("sourceRefId"),
        "chunk_id": source.get("chunkId"),
        "citation": json.dumps(source, ensure_ascii=False),
        "metadata": json.dumps(source.get("metadata") or {}, ensure_ascii=False),
    }


def asset_params(page_id, version_id, request_id, asset):
    return {
        "page_id": page_id,
        "version_id": version_id,
        "request_id": request_id,
        "asset_type": asset.get("assetType", "image"),
        "prompt": asset.get("prompt"),
        "storage_path": asset.get("storagePath") or f"prompt-only://{asset.get('slot', 'asset')}",
        "public_url": asset.get("publicUrl"),
        "status": asset.get("status", "queued"),
        "metadata": json.dumps({"slot": asset.get("slot"), **(asset.get("metadata") or {})}, ensure_ascii=False),
    }


def request_status(page_status: str) -> str:
    if page_status in {"rejected", "no_data", "failed"}:
        return page_status
    return "completed"
