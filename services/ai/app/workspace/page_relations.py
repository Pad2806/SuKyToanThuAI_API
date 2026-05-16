from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.workspace.page_rows import asset_params, source_params


async def save_sources(db: AsyncSession, page_id, version_id, request_id, sources) -> None:
    for source in sources:
        await db.execute(
            text(
                """
                INSERT INTO public.user_page_sources
                  (page_id, request_id, version_id, source_type, source_id, source_ref_type, source_ref_id, chunk_id, citation_json, metadata)
                VALUES (:page_id, :request_id, :version_id, :source_type, :source_id, :source_ref_type, :source_ref_id, :chunk_id, CAST(:citation AS jsonb), CAST(:metadata AS jsonb))
                """
            ),
            source_params(page_id, version_id, request_id, source),
        )


async def save_assets(db: AsyncSession, page_id, version_id, request_id, assets) -> None:
    for asset in assets:
        await db.execute(
            text(
                """
                INSERT INTO public.user_page_assets
                  (page_id, version_id, request_id, asset_type, prompt, storage_path, public_url, status, metadata)
                VALUES (:page_id, :version_id, :request_id, :asset_type, :prompt, :storage_path, :public_url, :status, CAST(:metadata AS jsonb))
                """
            ),
            asset_params(page_id, version_id, request_id, asset),
        )
    await db.execute(
        text("UPDATE public.user_pages SET current_version_id = :version_id WHERE id = :page_id"),
        {"version_id": version_id, "page_id": page_id},
    )
