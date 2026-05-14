"""Job runner — polls generation_jobs and dispatches to handlers.

Job claiming uses SELECT ... FOR UPDATE SKIP LOCKED for safe concurrency.
"""
import asyncio
import logging
import uuid
from datetime import timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal

log = logging.getLogger("job-runner")


class JobRunner:
    def __init__(self, config):
        self.config = config
        self.worker_id = config.WORKER_ID
        self.poll_interval = config.WORKER_POLL_INTERVAL_SECONDS
        self.lock_timeout = config.WORKER_JOB_LOCK_TIMEOUT_MINUTES

    async def start(self):
        log.info(f"JobRunner started. worker_id={self.worker_id}")
        while True:
            async with AsyncSessionLocal() as db:
                try:
                    processed = await self._poll(db)
                    if not processed:
                        await asyncio.sleep(self.poll_interval)
                except Exception as e:
                    log.exception(f"Poll cycle error: {e}")
                    await asyncio.sleep(self.poll_interval)

    async def _poll(self, db: AsyncSession) -> bool:
        row = await db.execute(
            text("""
                UPDATE ai.generation_jobs
                SET status    = 'running',
                    locked_by = :worker_id,
                    locked_at = now(),
                    started_at = now(),
                    attempts   = attempts + 1
                WHERE id = (
                    SELECT id FROM ai.generation_jobs
                    WHERE status = 'queued'
                      AND (
                        locked_at IS NULL
                        OR locked_at < now() - (:timeout_min || ' minutes')::interval
                      )
                    ORDER BY queued_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                RETURNING id, type, input
            """),
            {"worker_id": self.worker_id, "timeout_min": self.lock_timeout},
        )
        await db.commit()
        job = row.fetchone()

        if not job:
            return False

        job_id, job_type, job_input = str(job[0]), job[1], job[2]
        log.info(f"Claimed job {job_id} type={job_type}")

        try:
            output = await self._dispatch(job_type, job_input, db)
            await db.execute(
                text("""
                    UPDATE ai.generation_jobs
                    SET status='succeeded', output=:out::jsonb, finished_at=now()
                    WHERE id=:id
                """),
                {"out": str(output), "id": job_id},
            )
            await db.commit()
            log.info(f"Job {job_id} succeeded")
        except Exception as exc:
            log.exception(f"Job {job_id} failed: {exc}")
            await db.execute(
                text("""
                    UPDATE ai.generation_jobs
                    SET status = CASE WHEN attempts >= max_attempts THEN 'failed' ELSE 'queued' END,
                        error  = :error,
                        locked_by = NULL, locked_at = NULL,
                        finished_at = CASE WHEN attempts >= max_attempts THEN now() ELSE NULL END
                    WHERE id = :id
                """),
                {"error": str(exc)[:2000], "id": job_id},
            )
            await db.commit()

        return True

    async def _dispatch(self, job_type: str, job_input: dict, db: AsyncSession):
        from app.handlers.document_ingestion import handle_document_ingestion
        from app.handlers.story_generation import handle_story_generation
        from app.handlers.image_generation import handle_image_generation

        handlers = {
            "document_ingestion": handle_document_ingestion,
            "story_generation": handle_story_generation,
            "image_generation": handle_image_generation,
        }
        handler = handlers.get(job_type)
        if not handler:
            raise ValueError(f"Unknown job type: {job_type}")
        return await handler(job_input, self.config)
