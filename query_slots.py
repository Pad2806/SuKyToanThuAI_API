import asyncio
import json
import os

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres.xqzpssxlxbnwdtjrpkzv:Anhdung10!@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")

async def main():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT slot_key, image_url FROM public.admin_event_asset_slots "
                "WHERE event_id LIKE :pattern"
            ),
            {"pattern": "%dien-bien-phu-tren-khong%"},
        )
        rows = result.mappings().all()
        print(json.dumps([dict(r) for r in rows], indent=2))

    await engine.dispose()

asyncio.run(main())
