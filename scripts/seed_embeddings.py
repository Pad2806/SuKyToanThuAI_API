import asyncio
import os
from typing import Any

import asyncpg
import httpx

from seed_files import database_url


async def main() -> None:
    conn = await asyncpg.connect(dsn=database_url())
    try:
        units = await conn.fetch(
            """
            SELECT id, title, body, grade_tags, event_slugs
            FROM public.official_text_units
            WHERE status = 'published'
            ORDER BY id
            """
        )
        chunks = []
        for unit in units:
            document_id = await upsert_document(conn, unit)
            for index, content in enumerate(split_chunks(unit["body"])):
                chunk_id = await upsert_chunk(conn, document_id, unit, index, content)
                chunks.append((chunk_id, content))
        if os.getenv("OPENAI_API_KEY") and chunks:
            await embed_chunks(conn, chunks)
    finally:
        await conn.close()


async def upsert_document(conn: asyncpg.Connection, unit: asyncpg.Record) -> str:
    existing = await conn.fetchrow(
        """
        SELECT id FROM public.rag_source_documents
        WHERE source_ref_type = 'official_text_unit' AND source_ref_id = $1
        LIMIT 1
        """,
        unit["id"],
    )
    if existing:
        return str(existing["id"])
    row = await conn.fetchrow(
        """
        INSERT INTO public.rag_source_documents
          (title, source_scope, owner_service, source_ref_type, source_ref_id,
           grade_tags, status)
        VALUES ($1,'official','content','official_text_unit',$2,$3,'ready')
        RETURNING id
        """,
        unit["title"],
        unit["id"],
        unit["grade_tags"],
    )
    return str(row["id"])


async def upsert_chunk(
    conn: asyncpg.Connection,
    document_id: str,
    unit: asyncpg.Record,
    index: int,
    content: str,
) -> str:
    row = await conn.fetchrow(
        """
        INSERT INTO public.rag_document_chunks
          (document_id, chunk_index, content, token_count, source_ref_type, source_ref_id)
        VALUES ($1,$2,$3,$4,'official_text_unit',$5)
        ON CONFLICT (document_id, chunk_index) DO UPDATE SET content=EXCLUDED.content
        RETURNING id
        """,
        document_id,
        index,
        content,
        max(1, len(content) // 4),
        unit["id"],
    )
    return str(row["id"])


async def embed_chunks(conn: asyncpg.Connection, chunks: list[tuple[str, str]]) -> None:
    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    embeddings = await embed_texts([content for _, content in chunks], model)
    for (chunk_id, _), embedding in zip(chunks, embeddings, strict=False):
        await conn.execute(
            """
            INSERT INTO public.rag_chunk_embeddings
              (chunk_id, embedding, embedding_model, embedding_dim)
            VALUES ($1,$2,$3,$4)
            ON CONFLICT (chunk_id) DO UPDATE SET
              embedding=EXCLUDED.embedding, embedding_model=EXCLUDED.embedding_model,
              embedding_dim=EXCLUDED.embedding_dim
            """,
            chunk_id,
            vector_literal(embedding),
            model,
            len(embedding),
        )


async def embed_texts(texts: list[str], model: str) -> list[list[float]]:
    async with httpx.AsyncClient(
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.9router.com/v1").rstrip("/"),
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        timeout=60.0,
    ) as client:
        response = await client.post("/embeddings", json={"model": model, "input": texts})
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return [item["embedding"] for item in data["data"]]


def split_chunks(value: str, size: int = 1800) -> list[str]:
    paragraphs = [item.strip() for item in value.split("\n") if item.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) > size and current:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    return chunks + ([current] if current else [])


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(value) for value in values) + "]"


if __name__ == "__main__":
    asyncio.run(main())
