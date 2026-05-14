"""AI Worker — entry point.

Runs as a background process (no HTTP server needed for Phase 1).
Polls ai.generation_jobs table and dispatches to handlers.
"""
import asyncio
import os

from app.core.config import config
from shared.logging import setup_logging

log = setup_logging("ai-worker")


async def run():
    log.info(f"AI Worker starting. ID={config.WORKER_ID}, poll={config.WORKER_POLL_INTERVAL_SECONDS}s")
    from app.services.job_runner import JobRunner
    runner = JobRunner(config)
    await runner.start()


if __name__ == "__main__":
    asyncio.run(run())
