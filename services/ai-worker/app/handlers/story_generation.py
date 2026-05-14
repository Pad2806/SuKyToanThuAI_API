"""Handler stubs — Phase 1 scaffolding. Implement each in Phase 2."""
import logging

log = logging.getLogger("handlers")


async def handle_document_ingestion(job_input: dict, config) -> dict:
    """Parse → Chunk → Embed document. Phase 2 implementation."""
    document_id = job_input.get("document_id")
    log.info(f"[STUB] document_ingestion: document_id={document_id}")
    # TODO Phase 2: implement full ingest pipeline
    return {"status": "stub", "document_id": document_id}


async def handle_story_generation(job_input: dict, config) -> dict:
    """RAG retrieve → LLM generate → save story version. Phase 2."""
    event_id = job_input.get("event_id")
    log.info(f"[STUB] story_generation: event_id={event_id}")
    # TODO Phase 2: implement full story generation pipeline
    return {"status": "stub", "event_id": event_id}


async def handle_image_generation(job_input: dict, config) -> dict:
    """Generate image via AI → upload to S3 → create review item. Phase 2."""
    prompt = job_input.get("prompt", "")
    log.info(f"[STUB] image_generation: prompt={prompt[:50]}")
    # TODO Phase 2: implement full image generation pipeline
    return {"status": "stub"}
