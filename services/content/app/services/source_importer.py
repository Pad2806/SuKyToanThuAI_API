import hashlib
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.text_chunker import TextChunk
from app.services.vertex_embedding_client import VertexEmbeddingClient


class SourceImporter:
    def __init__(self, embedder: VertexEmbeddingClient | None = None) -> None:
        self.embedder = embedder or VertexEmbeddingClient()

    async def import_chunks(
        self,
        db: AsyncSession,
        *,
        event_id: str,
        title: str,
        chunks: list[TextChunk],
        metadata: dict[str, Any],
        grade_tags: list[str],
    ) -> dict[str, Any]:
        if not chunks:
            raise ValueError("Source has no readable content")

        document_id = await self._create_document(db, event_id, title, metadata, grade_tags)
        embeddings = await self.embedder.embed_texts([chunk.content for chunk in chunks])
        for index, chunk in enumerate(chunks):
            chunk_id = await self._upsert_chunk(db, document_id, index, chunk)
            await self._upsert_embedding(db, chunk_id, embeddings[index])
        await db.execute(
            text("UPDATE public.rag_source_documents SET status = 'ready' WHERE id = :id"),
            {"id": document_id},
        )
        return {"id": str(document_id), "title": title, "chunkCount": len(chunks), "status": "ready"}

    async def _create_document(
        self,
        db: AsyncSession,
        event_id: str,
        title: str,
        metadata: dict[str, Any],
        grade_tags: list[str],
    ):
        result = await db.execute(
            text(
                """
                INSERT INTO public.rag_source_documents
                  (title, source_scope, owner_service, source_ref_type, source_ref_id,
                   grade_tags, metadata, status)
                VALUES (:title, 'official', 'content', 'admin_event_source', :event_id,
                  :grade_tags, CAST(:metadata AS jsonb), 'embedding_pending')
                RETURNING id
                """
            ),
            {
                "title": title,
                "event_id": event_id,
                "grade_tags": grade_tags,
                "metadata": json.dumps({"eventId": event_id, **metadata}),
            },
        )
        return result.scalar_one()

    async def _upsert_chunk(
        self,
        db: AsyncSession,
        document_id,
        index: int,
        chunk: TextChunk,
    ):
        result = await db.execute(
            text(
                """
                INSERT INTO public.rag_document_chunks
                  (document_id, chunk_index, content, token_count, content_hash,
                   source_ref_type, source_ref_id, metadata)
                VALUES (:document_id, :chunk_index, :content, :token_count, :content_hash,
                  'admin_event_source', :document_id_text, CAST(:metadata AS jsonb))
                RETURNING id
                """
            ),
            {
                "document_id": document_id,
                "document_id_text": str(document_id),
                "chunk_index": index,
                "content": chunk.content,
                "token_count": max(1, len(chunk.content) // 4),
                "content_hash": hashlib.sha256(chunk.content.encode("utf-8")).hexdigest(),
                "metadata": json.dumps(chunk.metadata),
            },
        )
        return result.scalar_one()

    async def _upsert_embedding(self, db: AsyncSession, chunk_id, embedding: list[float]) -> None:
        await db.execute(
            text(
                """
                INSERT INTO public.rag_chunk_embeddings
                  (chunk_id, embedding, embedding_model, embedding_dim)
                VALUES (:chunk_id, CAST(:embedding AS vector), :model, :dim)
                ON CONFLICT (chunk_id) DO UPDATE SET
                  embedding = EXCLUDED.embedding,
                  embedding_model = EXCLUDED.embedding_model,
                  embedding_dim = EXCLUDED.embedding_dim
                """
            ),
            {
                "chunk_id": chunk_id,
                "embedding": _vector_literal(embedding),
                "model": self.embedder.settings.ai_embedding_model,
                "dim": len(embedding),
            },
        )


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(value) for value in values) + "]"
