import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.workspace.page_relations import save_assets, save_sources
from app.workspace.page_rows import page_detail, page_summary, request_status
from app.workspace.story_event_payload import assign_page_identity


class PageManager:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_request(
        self,
        user_id: UUID,
        flow_type: str,
        intent: str,
        template: str,
        query_text: str | None = None,
        input_text: str | None = None,
    ) -> UUID:
        row = (await self.db.execute(
            text(
                """
                INSERT INTO public.generation_requests
                  (user_id, flow_type, intent, template_key, query_text, input_text, status)
                VALUES (:user_id, :flow_type, :intent, :template, :query_text, :input_text, 'processing')
                RETURNING id
                """
            ),
            {"user_id": user_id, "flow_type": flow_type, "intent": intent, "template": template, "query_text": query_text, "input_text": input_text},
        )).mappings().one()
        return row["id"]

    async def finish_request(
        self,
        request_id: UUID | None,
        status: str,
        page_id: UUID | None = None,
        moderation_status: str | None = None,
        failure_reason: str | None = None,
    ) -> None:
        if request_id is None:
            return
        await self.db.execute(
            text(
                """
                UPDATE public.generation_requests
                SET status = :status, result_page_id = :page_id,
                    moderation_status = COALESCE(:moderation_status, moderation_status),
                    failure_reason = :failure_reason, completed_at = now(), updated_at = now()
                WHERE id = :request_id
                """
            ),
            {"request_id": request_id, "status": status, "page_id": page_id, "moderation_status": moderation_status, "failure_reason": failure_reason},
        )

    async def save_story_event_page(
        self,
        user_id: UUID,
        title: str,
        flow_type: str,
        source_mode: str,
        template: str,
        render_payload: dict[str, Any],
        parsed_content_json: dict[str, Any] | None = None,
        sources: list[dict[str, Any]] | None = None,
        request_id: UUID | None = None,
        status: str = "completed",
        page_id: UUID | None = None,
    ) -> dict:
        if page_id is None:
            page = await self._insert_page(user_id, title, flow_type, source_mode, template, request_id, status)
            page_id = page["id"]
        else:
            await self._update_page(page_id, user_id, title, status)

        payload = assign_page_identity(render_payload, page_id)
        version = await self._insert_version(page_id, request_id, payload, parsed_content_json or {}, status)
        await save_sources(self.db, page_id, version["id"], request_id, sources or payload.get("citations") or [])
        await save_assets(self.db, page_id, version["id"], request_id, payload.get("assets") or [])
        if status != "needs_user_confirmation":
            await self.finish_request(request_id, request_status(status), page_id, payload.get("moderation", {}).get("status"))
        await self.db.commit()
        return await self.get_page(page_id, user_id) or {}

    async def save_pending_page(
        self,
        user_id: UUID,
        title: str,
        template: str,
        render_payload: dict[str, Any],
        parsed_content_json: dict[str, Any],
        request_id: UUID | None,
    ) -> dict:
        return await self.save_story_event_page(
            user_id=user_id,
            title=title,
            flow_type="custom_content",
            source_mode="creator",
            template=template,
            render_payload=render_payload,
            parsed_content_json=parsed_content_json,
            request_id=request_id,
            status="needs_user_confirmation",
        )

    async def get_pending_context(self, page_id: UUID, user_id: UUID) -> dict | None:
        row = (await self.db.execute(
            text(
                """
                SELECT p.id, p.request_id, p.template_key, p.current_version_id, v.parsed_content_json, v.render_payload
                FROM public.user_pages p
                JOIN public.user_page_versions v ON v.id = p.current_version_id
                WHERE p.id = :page_id AND p.user_id = :user_id AND p.status = 'needs_user_confirmation'
                LIMIT 1
                """
            ),
            {"page_id": page_id, "user_id": user_id},
        )).mappings().first()
        return dict(row) if row else None

    async def list_pages(self, user_id: UUID, limit: int = 20, offset: int = 0, source_mode: str | None = None) -> list[dict]:
        source_filter = "AND p.source_payload->>'sourceMode' = :source_mode" if source_mode else ""
        result = await self.db.execute(
            text(
                f"""
                SELECT p.id, p.title, p.template_key, p.flow_type, p.status, p.created_at,
                       p.source_payload, v.render_payload
                FROM public.user_pages p
                LEFT JOIN public.user_page_versions v ON v.id = p.current_version_id
                WHERE p.user_id = :user_id {source_filter}
                ORDER BY p.created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"user_id": user_id, "limit": limit, "offset": offset, "source_mode": source_mode},
        )
        return [page_summary(row) for row in result.mappings().all()]

    async def get_page(self, page_id: UUID, user_id: UUID) -> dict | None:
        row = (await self.db.execute(
            text(
                """
                SELECT p.id, p.title, p.template_key, p.flow_type, p.status, p.created_at,
                       p.source_payload, v.render_payload
                FROM public.user_pages p
                LEFT JOIN public.user_page_versions v ON v.id = p.current_version_id
                WHERE p.id = :page_id AND p.user_id = :user_id
                LIMIT 1
                """
            ),
            {"page_id": page_id, "user_id": user_id},
        )).mappings().first()
        return page_detail(row) if row else None

    async def _insert_page(self, user_id, title, flow_type, source_mode, template, request_id, status):
        return (await self.db.execute(
            text(
                """
                INSERT INTO public.user_pages
                  (user_id, request_id, flow_type, intent, title, template_key, source_payload, status)
                VALUES (:user_id, :request_id, :flow_type, 'generate_page', :title, :template,
                        CAST(:source_payload AS jsonb), :status)
                RETURNING id
                """
            ),
            {"user_id": user_id, "request_id": request_id, "flow_type": flow_type, "title": title, "template": template, "source_payload": json.dumps({"sourceMode": source_mode}, ensure_ascii=False), "status": status},
        )).mappings().one()

    async def _update_page(self, page_id, user_id, title, status):
        await self.db.execute(
            text("UPDATE public.user_pages SET title = :title, status = :status, updated_at = now() WHERE id = :page_id AND user_id = :user_id"),
            {"page_id": page_id, "user_id": user_id, "title": title, "status": status},
        )

    async def _insert_version(self, page_id, request_id, payload, parsed, status):
        return (await self.db.execute(
            text(
                """
                INSERT INTO public.user_page_versions
                  (page_id, request_id, version_number, render_payload, page_json, parsed_content_json, status)
                VALUES (:page_id, :request_id,
                  COALESCE((SELECT max(version_number) + 1 FROM public.user_page_versions WHERE page_id = :page_id), 1),
                  CAST(:payload AS jsonb), CAST(:payload AS jsonb), CAST(:parsed AS jsonb), :status)
                RETURNING id
                """
            ),
            {"page_id": page_id, "request_id": request_id, "payload": json.dumps(payload, ensure_ascii=False), "parsed": json.dumps(parsed, ensure_ascii=False), "status": "draft" if status == "needs_user_confirmation" else "generated"},
        )).mappings().one()
