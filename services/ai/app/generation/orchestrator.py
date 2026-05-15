from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.generation.prompts import CREATOR_SYSTEM, CREATOR_USER, RESEARCH_SYSTEM, RESEARCH_USER
from app.providers.openai_client import OpenAIClient
from app.rag.retriever import ChunkResult, retrieve
from app.workspace.page_manager import PageManager


class GenerationOrchestrator:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.page_manager = PageManager(db)

    async def research(self, query: str, template: str, user_id: UUID) -> dict:
        chunks = await retrieve(query, self.db)
        if not chunks:
            content = "Không tìm thấy dữ liệu phù hợp trong kho sử liệu hiện có."
            return await self.page_manager.save_page(
                user_id=user_id,
                title=f"Kết quả: {query[:80]}",
                content=content,
                sources=[],
                template=template,
                flow_type="system_data",
            )

        context = "\n\n".join(f"[{item.title}]\n{item.content[:1600]}" for item in chunks)
        content = await self._chat_or_fallback(
            [
                {"role": "system", "content": RESEARCH_SYSTEM},
                {"role": "user", "content": RESEARCH_USER.format(context=context, query=query)},
            ],
            fallback=_fallback_research(query, chunks),
        )
        return await self.page_manager.save_page(
            user_id=user_id,
            title=f"Kết quả: {query[:80]}",
            content=content,
            sources=_source_slugs(chunks),
            template=template,
            flow_type="system_data",
        )

    async def create(self, content: str, template: str, user_id: UUID) -> dict:
        if len(content.strip()) < 50:
            raise HTTPException(status_code=400, detail="Nội dung quá ngắn. Tối thiểu 50 ký tự.")
        generated = await self._chat_or_fallback(
            [
                {"role": "system", "content": CREATOR_SYSTEM},
                {"role": "user", "content": CREATOR_USER.format(content=content)},
            ],
            fallback=_fallback_creator(content),
        )
        return await self.page_manager.save_page(
            user_id=user_id,
            title=_title_from_content(content),
            content=generated,
            sources=[],
            template=template,
            flow_type="custom_content",
        )

    async def _chat_or_fallback(self, messages: list[dict[str, str]], fallback: str) -> str:
        if not settings.openai_api_key or settings.openai_api_key == "sk-xxx":
            return fallback
        client = OpenAIClient(settings.openai_api_key, settings.openai_base_url)
        try:
            return await client.chat(messages, model=settings.openai_chat_model)
        except Exception:
            return fallback
        finally:
            await client.close()


def _fallback_research(query: str, chunks: list[ChunkResult]) -> str:
    lead = chunks[0].content.strip().split("\n")[0]
    sources = ", ".join(item.title for item in chunks[:3])
    return f"Với câu hỏi '{query}', dữ liệu liên quan nhất là: {sources}. {lead}"


def _fallback_creator(content: str) -> str:
    return f"Bản nháp lịch sử:\n\n{content.strip()}"


def _source_slugs(chunks: list[ChunkResult]) -> list[str]:
    return sorted({slug for item in chunks for slug in item.event_slugs})


def _title_from_content(content: str) -> str:
    first_line = content.strip().splitlines()[0]
    return first_line[:80] if first_line else "Trang lịch sử mới"
