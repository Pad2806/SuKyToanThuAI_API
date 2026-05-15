import json
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PageManager:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def save_page(
        self,
        user_id: UUID,
        title: str,
        content: str,
        sources: list[str],
        template: str,
        flow_type: str,
    ) -> dict:
        page = (
            await self.db.execute(
                text(
                    """
                    INSERT INTO public.user_pages
                      (user_id, flow_type, intent, title, template_key, source_payload, status)
                    VALUES (:user_id, :flow_type, 'generate_page', :title, :template,
                            CAST(:source_payload AS jsonb), 'completed')
                    RETURNING id, created_at
                    """
                ),
                {
                    "user_id": user_id,
                    "flow_type": flow_type,
                    "title": title,
                    "template": template,
                    "source_payload": json.dumps({"sources": sources}, ensure_ascii=False),
                },
            )
        ).mappings().one()
        render_payload = {"title": title, "content": content, "sources": sources, "template": template}
        version = (
            await self.db.execute(
                text(
                    """
                    INSERT INTO public.user_page_versions
                      (page_id, version_number, render_payload, page_json, parsed_content_json)
                    VALUES (:page_id, 1, CAST(:payload AS jsonb), CAST(:payload AS jsonb), '{}'::jsonb)
                    RETURNING id
                    """
                ),
                {"page_id": page["id"], "payload": json.dumps(render_payload, ensure_ascii=False)},
            )
        ).mappings().one()
        await self.db.execute(
            text("UPDATE public.user_pages SET current_version_id = :version_id WHERE id = :page_id"),
            {"version_id": version["id"], "page_id": page["id"]},
        )
        await self.db.commit()
        return {"id": page["id"], **render_payload}

    async def list_pages(self, user_id: UUID, limit: int = 20, offset: int = 0) -> list[dict]:
        result = await self.db.execute(
            text(
                """
                SELECT p.id, p.title, p.template_key, p.flow_type, p.status, p.created_at,
                       v.render_payload
                FROM public.user_pages p
                LEFT JOIN public.user_page_versions v ON v.id = p.current_version_id
                WHERE p.user_id = :user_id
                ORDER BY p.created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"user_id": user_id, "limit": limit, "offset": offset},
        )
        return [_page_summary(row) for row in result.mappings().all()]

    async def get_page(self, page_id: UUID, user_id: UUID) -> dict | None:
        result = await self.db.execute(
            text(
                """
                SELECT p.id, p.title, p.template_key, p.flow_type, p.status, p.created_at,
                       v.render_payload
                FROM public.user_pages p
                LEFT JOIN public.user_page_versions v ON v.id = p.current_version_id
                WHERE p.id = :page_id AND p.user_id = :user_id
                LIMIT 1
                """
            ),
            {"page_id": page_id, "user_id": user_id},
        )
        row = result.mappings().first()
        return _page_summary(row) if row else None


def _page_summary(row) -> dict:
    payload = row["render_payload"] or {}
    return {
        "id": row["id"],
        "title": row["title"],
        "content": payload.get("content", ""),
        "sources": payload.get("sources", []),
        "template": row["template_key"],
        "flowType": row["flow_type"],
        "status": row["status"],
        "createdAt": row["created_at"],
    }
