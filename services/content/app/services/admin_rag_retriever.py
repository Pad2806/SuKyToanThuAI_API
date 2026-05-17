from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class AdminChunk:
    id: str
    document_id: str
    title: str
    content: str
    metadata: dict


async def retrieve_admin_chunks(
    db: AsyncSession,
    event_id: str,
    source_ids: list[str],
    limit: int = 12,
) -> list[AdminChunk]:
    source_filter = "AND d.id = ANY(:source_ids)" if source_ids else ""
    result = await db.execute(
        text(
            f"""
            SELECT c.id, c.document_id, d.title, c.content, c.metadata
            FROM public.rag_document_chunks c
            JOIN public.rag_source_documents d ON d.id = c.document_id
            WHERE d.source_ref_type = 'admin_event_source'
              AND d.source_ref_id = :event_id
              AND d.status = 'ready'
              {source_filter}
            ORDER BY c.chunk_index
            LIMIT :limit
            """
        ),
        {"event_id": event_id, "source_ids": source_ids, "limit": limit},
    )
    return [
        AdminChunk(
            id=str(row["id"]),
            document_id=str(row["document_id"]),
            title=row["title"],
            content=row["content"],
            metadata=dict(row["metadata"] or {}),
        )
        for row in result.mappings().all()
    ]
