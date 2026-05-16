from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.generation.story_event_generator import (
    parse_creator_content,
    payload_from_creator,
    payload_from_research,
)
from app.safety.content_moderation import moderate_text
from app.safety.coverage_gate import accepted_coverage_report, check_story_event_coverage
from app.rag.retriever import retrieve
from app.workspace.page_manager import PageManager
from app.workspace.story_event_payload import story_event_shell


class GenerationOrchestrator:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.page_manager = PageManager(db)

    async def research(self, query: str, template: str, user_id: UUID) -> dict:
        request_id = await self.page_manager.create_request(
            user_id=user_id,
            flow_type="system_data",
            intent="generate_page",
            template=template,
            query_text=query,
        )
        chunks = await retrieve(query, self.db)
        if not chunks:
            await self.page_manager.finish_request(request_id, "no_data", failure_reason="Không tìm thấy dữ liệu phù hợp.")
            await self.db.commit()
            return {
                "status": "no_data",
                "detail": "Không tìm thấy dữ liệu phù hợp trong kho sử liệu hiện có.",
            }

        payload = payload_from_research(query, chunks, template)
        return await self.page_manager.save_story_event_page(
            user_id=user_id,
            title=payload["title"],
            flow_type="system_data",
            source_mode="research",
            template=template,
            render_payload=payload,
            parsed_content_json={"query": query, "chunkIds": [str(chunk.id) for chunk in chunks]},
            sources=payload.get("citations", []),
            request_id=request_id,
        )

    async def create(self, content: str, template: str, user_id: UUID) -> dict:
        if len(content.strip()) < 50:
            raise HTTPException(status_code=400, detail="Nội dung quá ngắn. Tối thiểu 50 ký tự.")

        request_id = await self.page_manager.create_request(
            user_id=user_id,
            flow_type="custom_content",
            intent="parse_and_render",
            template=template,
            input_text=content,
        )
        moderation = moderate_text(content)
        if moderation.status == "rejected":
            payload = story_event_shell("Nội dung bị từ chối", template, "custom_content", "creator")
            payload["moderation"] = {"status": "rejected", "reason": moderation.reason}
            page = await self.page_manager.save_story_event_page(
                user_id=user_id,
                title="Nội dung bị từ chối",
                flow_type="custom_content",
                source_mode="creator",
                template=template,
                render_payload=payload,
                parsed_content_json={"inputLength": len(content)},
                request_id=request_id,
                status="rejected",
            )
            return {"status": "rejected", "id": page.get("id"), "moderation": payload["moderation"]}

        parsed = parse_creator_content(content, template)
        coverage = check_story_event_coverage(parsed, template)
        if coverage["missing"]:
            payload = story_event_shell(parsed["title"], template, "custom_content", "creator", parsed["summary"])
            payload["coverageReport"] = coverage
            payload["moderation"] = {"status": "approved", "reason": None}
            page = await self.page_manager.save_pending_page(
                user_id=user_id,
                title=parsed["title"],
                template=template,
                render_payload=payload,
                parsed_content_json={"parsed": parsed, "coverageReport": coverage},
                request_id=request_id,
            )
            return {
                "status": "needs_user_confirmation",
                "id": page.get("id"),
                "coverageReport": coverage,
                "moderation": payload["moderation"],
            }

        payload = payload_from_creator(parsed, template, coverage)
        return await self.page_manager.save_story_event_page(
            user_id=user_id,
            title=payload["title"],
            flow_type="custom_content",
            source_mode="creator",
            template=template,
            render_payload=payload,
            parsed_content_json={"parsed": parsed, "coverageReport": coverage},
            request_id=request_id,
        )

    async def confirm_missing(self, page_id: UUID, user_id: UUID) -> dict:
        context = await self.page_manager.get_pending_context(page_id, user_id)
        if context is None:
            raise HTTPException(status_code=404, detail="Pending page not found")

        parsed_content = context["parsed_content_json"] or {}
        parsed = parsed_content.get("parsed") or {}
        coverage = accepted_coverage_report(parsed_content.get("coverageReport") or {})
        payload = payload_from_creator(parsed, context["template_key"] or "universal", coverage)
        return await self.page_manager.save_story_event_page(
            user_id=user_id,
            title=payload["title"],
            flow_type="custom_content",
            source_mode="creator",
            template=context["template_key"] or "universal",
            render_payload=payload,
            parsed_content_json={"parsed": parsed, "coverageReport": coverage},
            request_id=context["request_id"],
            page_id=page_id,
        )
