from dataclasses import dataclass, field
from io import BytesIO


@dataclass
class TextChunk:
    content: str
    metadata: dict = field(default_factory=dict)


def chunk_text(
    value: str,
    *,
    max_chars: int = 1800,
    metadata: dict | None = None,
) -> list[TextChunk]:
    base_metadata = metadata or {}
    paragraphs = [item.strip() for item in value.splitlines() if item.strip()]
    chunks: list[TextChunk] = []
    current = ""
    for paragraph in paragraphs:
        next_value = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(next_value) > max_chars and current:
            chunks.append(TextChunk(current, dict(base_metadata)))
            current = paragraph
        else:
            current = next_value
    if current:
        chunks.append(TextChunk(current, dict(base_metadata)))
    return chunks


def extract_pdf_chunks(raw: bytes, *, max_chars: int = 1800, metadata: dict | None = None) -> list[TextChunk]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF extraction dependency is not installed") from exc

    reader = PdfReader(BytesIO(raw))
    if reader.is_encrypted:
        raise ValueError("Encrypted PDF files are not supported")

    chunks: list[TextChunk] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        page_metadata = {**(metadata or {}), "pageFrom": index, "pageTo": index}
        chunks.extend(chunk_text(text, max_chars=max_chars, metadata=page_metadata))
    if not chunks:
        raise ValueError("No readable text found in PDF")
    return chunks
