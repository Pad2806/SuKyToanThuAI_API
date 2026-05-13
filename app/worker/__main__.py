"""
PostgreSQL-based Worker — python -m app.worker

Design:
  - No Redis, no Celery, no RQ.
  - Polls generation_jobs every WORKER_POLL_INTERVAL_SECONDS seconds.
  - Uses SELECT FOR UPDATE SKIP LOCKED to safely claim jobs across multiple worker instances.
  - Handles three job types: 'ingest', 'story_version', 'image'.
  - On failure: retries up to max_attempts, then marks 'failed'.
"""
import asyncio
import logging
import signal
import uuid
from datetime import datetime, timezone

from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import GenerationJob

logger = logging.getLogger(__name__)
_shutdown = False


def _handle_signal(sig, frame):
    global _shutdown
    logger.info("Worker received signal %s — shutting down gracefully.", sig)
    _shutdown = True


# ─────────────────────────────────────────────
#  Job Claim
# ─────────────────────────────────────────────

CLAIM_SQL = text("""
    WITH claimed AS (
        SELECT id FROM generation_jobs
        WHERE status = 'queued'
          AND (locked_at IS NULL
               OR locked_at < now() - INTERVAL ':timeout_minutes minutes')
        ORDER BY queued_at
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    )
    UPDATE generation_jobs
    SET status    = 'running',
        locked_by = :worker_id,
        locked_at = now(),
        started_at = COALESCE(started_at, now()),
        attempts  = attempts + 1
    FROM claimed
    WHERE generation_jobs.id = claimed.id
    RETURNING generation_jobs.*
""")


async def claim_next_job(db: AsyncSession) -> GenerationJob | None:
    result = await db.execute(
        CLAIM_SQL,
        {
            "worker_id": settings.WORKER_ID,
            "timeout_minutes": settings.WORKER_JOB_LOCK_TIMEOUT_MINUTES,
        },
    )
    row = result.mappings().first()
    if row is None:
        return None
    await db.commit()
    return GenerationJob(**dict(row))


# ─────────────────────────────────────────────
#  Job Completion
# ─────────────────────────────────────────────

async def mark_succeeded(db: AsyncSession, job_id: uuid.UUID, output: dict) -> None:
    await db.execute(
        update(GenerationJob)
        .where(GenerationJob.id == job_id)
        .values(
            status="succeeded",
            finished_at=datetime.now(timezone.utc),
            output=output,
            locked_by=None,
            locked_at=None,
        )
    )
    await db.commit()


async def mark_failed(db: AsyncSession, job: GenerationJob, error: str) -> None:
    if job.attempts < job.max_attempts:
        new_status = "queued"
        finished_at = None
    else:
        new_status = "failed"
        finished_at = datetime.now(timezone.utc)

    await db.execute(
        update(GenerationJob)
        .where(GenerationJob.id == job.id)
        .values(
            status=new_status,
            error=error,
            finished_at=finished_at,
            locked_by=None,
            locked_at=None,
        )
    )
    await db.commit()


# ─────────────────────────────────────────────
#  Handlers (stubs — implement in Phase 2)
# ─────────────────────────────────────────────

async def handle_ingest(db: AsyncSession, job: GenerationJob) -> dict:
    """Chunk + embed a source document."""
    # Phase 2 implementation:
    # 1. Load source_document from job.source_document_id
    # 2. Download raw file from S3
    # 3. Split into chunks (overlap 50 tokens)
    # 4. For each chunk: call ai_client.embed(chunk.content)
    # 5. Batch insert document_chunks + chunk_embeddings
    # 6. Update source_document.status = 'embedded'
    raise NotImplementedError("IngestHandler not yet implemented (Phase 2)")


async def handle_story_version(db: AsyncSession, job: GenerationJob) -> dict:
    """RAG-based story generation."""
    # Phase 2 implementation:
    # 1. Load event + event_sources from job.event_id
    # 2. Embed event.summary → query_vec
    # 3. Vector search chunk_embeddings (cosine) → top-K chunks
    # 4. Build RAG prompt + call ai_client.generate_json(prompt, story_schema)
    # 5. Write story_json to event_story_versions
    # 6. Insert block_citations for each block
    # 7. Insert review_items (status='pending')
    raise NotImplementedError("StoryGenHandler not yet implemented (Phase 2)")


async def handle_image(db: AsyncSession, job: GenerationJob) -> dict:
    """AI image generation."""
    # Phase 2 implementation:
    # 1. Load image_asset from job.image_asset_id
    # 2. Call ai_client.generate_image(asset.prompt)
    # 3. Download generated image bytes
    # 4. Upload to S3 via storage_client.upload(...)
    # 5. Update image_assets.storage_url + status='pending' (awaits review)
    raise NotImplementedError("ImageGenHandler not yet implemented (Phase 2)")


HANDLERS = {
    "ingest": handle_ingest,
    "story_version": handle_story_version,
    "image": handle_image,
}


# ─────────────────────────────────────────────
#  Main Loop
# ─────────────────────────────────────────────

async def run_worker() -> None:
    logger.info("Worker %s starting. Poll interval: %ss",
                settings.WORKER_ID, settings.WORKER_POLL_INTERVAL_SECONDS)

    while not _shutdown:
        async with AsyncSessionLocal() as db:
            job = await claim_next_job(db)

            if job is None:
                await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
                continue

            logger.info("Claimed job %s (type=%s attempt=%d/%d)",
                        job.id, job.type, job.attempts, job.max_attempts)

            handler = HANDLERS.get(job.type)
            if handler is None:
                await mark_failed(db, job, f"Unknown job type: {job.type}")
                continue

            try:
                output = await handler(db, job)
                await mark_succeeded(db, job.id, output)
                logger.info("Job %s succeeded.", job.id)
            except NotImplementedError as exc:
                # Phase 1 stubs — treat as hard failure
                await mark_failed(db, job, str(exc))
                logger.warning("Job %s failed (not implemented): %s", job.id, exc)
            except Exception as exc:
                await mark_failed(db, job, repr(exc))
                logger.exception("Job %s failed with exception.", job.id)

    logger.info("Worker %s stopped.", settings.WORKER_ID)


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stdout,
    )

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    asyncio.run(run_worker())
