from dataclasses import dataclass
from typing import Any

from app.services.gemini_pdf_ocr_client import GeminiPdfOcrClient
from app.services.text_chunker import TextChunk, chunk_text, extract_pdf_chunks

MAX_SOURCE_BYTES = 8 * 1024 * 1024


@dataclass
class SourceExtractionResult:
    chunks: list[TextChunk]
    metadata: dict[str, Any]


class SourceExtractionService:
    def __init__(self, ocr_client: GeminiPdfOcrClient | None = None) -> None:
        self.ocr_client = ocr_client or GeminiPdfOcrClient()

    async def extract(self, *, file, text_value: str | None, metadata: dict[str, Any] | None = None) -> SourceExtractionResult:
        base = dict(metadata or {})
        if file:
            raw = await file.read()
            if len(raw) > MAX_SOURCE_BYTES:
                raise ValueError("Source file is too large")
            filename = file.filename or ""
            content_type = (file.content_type or "").lower()
            file_meta = {**base, "fileName": filename, "fileSize": len(raw), "contentType": content_type}
            if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
                return await self._extract_pdf(raw, filename=filename, metadata=file_meta, fallback_text=text_value)
            if content_type.startswith("text/") or filename.lower().endswith(".txt"):
                chunks = _tag_chunks(chunk_text(_decode_text_file(raw), metadata=file_meta), "txt")
                return _result(chunks, file_meta, "txt")
            raise ValueError("Only TXT and PDF source files are supported")
        if text_value and text_value.strip():
            chunks = _tag_chunks(chunk_text(text_value, metadata=base), "manual_text")
            return _result(chunks, base, "manual_text")
        raise ValueError("A source file or manual text is required")

    async def _extract_pdf(
        self,
        raw: bytes,
        *,
        filename: str,
        metadata: dict[str, Any],
        fallback_text: str | None = None,
    ) -> SourceExtractionResult:
        try:
            chunks = _tag_chunks(extract_pdf_chunks(raw, metadata=metadata), "pdf_text")
            return _result(chunks, metadata, "pdf_text", page_count=_page_count(chunks))
        except ValueError as exc:
            if "No readable text found in PDF" not in str(exc):
                raise
        try:
            payload = await self.ocr_client.extract_pages(raw, filename=filename)
        except RuntimeError as exc:
            if fallback_text and fallback_text.strip():
                chunks = _tag_chunks(chunk_text(fallback_text, metadata=metadata), "manual_text")
                return _result(chunks, metadata, "manual_text", warnings=[str(exc)])
            raise
        pages = [page for page in payload.get("pages") or [] if str(page.get("text") or "").strip()]
        if not pages:
            raise ValueError("No readable text found after Gemini OCR")

        chunks: list[TextChunk] = []
        for page in pages:
            page_number = int(page.get("page") or 0) or None
            page_meta = {**metadata, "pageFrom": page_number, "pageTo": page_number}
            chunks.extend(chunk_text(str(page.get("text") or ""), metadata=page_meta))
        chunks = _tag_chunks(chunks, "gemini_ocr")
        return _result(chunks, metadata, "gemini_ocr", page_count=len(pages), warnings=payload.get("warnings") or [])


def _tag_chunks(chunks: list[TextChunk], method: str) -> list[TextChunk]:
    for chunk in chunks:
        chunk.metadata = {**chunk.metadata, "extractionMethod": method}
    return chunks


def _decode_text_file(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("TXT source files must be UTF-8 encoded") from exc

def _result(
    chunks: list[TextChunk],
    metadata: dict[str, Any],
    method: str,
    *,
    page_count: int | None = None,
    warnings: list[str] | None = None,
) -> SourceExtractionResult:
    if not chunks:
        raise ValueError("Source has no readable content")
    result_metadata = {**metadata, "extractionMethod": method, "chunkCount": len(chunks), "warnings": warnings or []}
    if page_count is not None:
        result_metadata["pageCount"] = page_count
        result_metadata["readablePageCount"] = page_count
    return SourceExtractionResult(chunks=chunks, metadata=result_metadata)


def _page_count(chunks: list[TextChunk]) -> int:
    pages = {chunk.metadata.get("pageFrom") for chunk in chunks if chunk.metadata.get("pageFrom")}
    return len(pages) or 1
