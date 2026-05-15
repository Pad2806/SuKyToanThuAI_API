import hashlib
import json
from dataclasses import asdict, dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from common.redis.client import get_redis_client


@dataclass
class ChunkResult:
    id: str
    title: str
    content: str
    event_slugs: list[str]
    score: float


async def retrieve(query: str, db: AsyncSession, limit: int = 5) -> list[ChunkResult]:
    cache_key = f"rag:query:{hashlib.md5(query.encode('utf-8')).hexdigest()}:{limit}"
    cached = await _cache_get(cache_key)
    if cached:
        return [ChunkResult(**item) for item in cached]

    term = f"%{query.strip()}%"
    result = await db.execute(
        text(
            """
            SELECT id, title, body, event_slugs,
              CASE
                WHEN search_tsv @@ plainto_tsquery('simple', :query)
                THEN ts_rank(search_tsv, plainto_tsquery('simple', :query))
                ELSE 0
              END AS score
            FROM public.official_text_units
            WHERE status = 'published'
              AND (
                search_tsv @@ plainto_tsquery('simple', :query)
                OR title ILIKE :term
                OR summary ILIKE :term
                OR body ILIKE :term
              )
            ORDER BY score DESC, title ASC
            LIMIT :limit
            """
        ),
        {"query": query, "term": term, "limit": limit},
    )
    chunks = [
        ChunkResult(
            id=row["id"],
            title=row["title"],
            content=row["body"],
            event_slugs=list(row["event_slugs"] or []),
            score=float(row["score"] or 0),
        )
        for row in result.mappings().all()
    ]
    await _cache_set(cache_key, [asdict(item) for item in chunks])
    return chunks


async def _cache_get(key: str) -> list[dict] | None:
    try:
        raw = await get_redis_client().get(key)
    except Exception:
        return None
    return json.loads(raw) if raw else None


async def _cache_set(key: str, value: list[dict]) -> None:
    try:
        await get_redis_client().setex(key, 3600, json.dumps(value, ensure_ascii=False))
    except Exception:
        return

