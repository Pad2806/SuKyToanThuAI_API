"""Document parsers for RAG service.

Supports: .txt, .md (text-based), .pdf (via pymupdf).
Returns plain text for the chunker to process.
"""
from __future__ import annotations

import io
from abc import ABC, abstractmethod


class BaseParser(ABC):
    @abstractmethod
    def extract(self, content: bytes) -> str:
        """Extract plain text from raw file bytes."""


class TxtParser(BaseParser):
    def extract(self, content: bytes) -> str:
        return content.decode("utf-8", errors="replace")


class MarkdownParser(BaseParser):
    """Markdown is kept as-is so the chunker can split on ## headings."""
    def extract(self, content: bytes) -> str:
        return content.decode("utf-8", errors="replace")


class PdfParser(BaseParser):
    """Extract text from PDF using pymupdf (fitz).

    Preserves heading structure by detecting large/bold text blocks
    and converting them to markdown-style headings (## Heading).
    """

    def extract(self, content: bytes) -> str:
        try:
            import fitz  # pymupdf
        except ImportError as e:
            raise RuntimeError("pymupdf not installed. Add 'pymupdf' to requirements.txt.") from e

        doc = fitz.open(stream=io.BytesIO(content), filetype="pdf")
        pages: list[str] = []

        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            page_lines: list[str] = []

            for block in blocks:
                if block.get("type") != 0:  # skip image blocks
                    continue
                for line in block.get("lines", []):
                    line_text = " ".join(
                        span["text"] for span in line.get("spans", [])
                    ).strip()
                    if not line_text:
                        continue

                    # Detect headings: large font size OR all-caps short line
                    spans = line.get("spans", [])
                    avg_size = (
                        sum(s.get("size", 12) for s in spans) / len(spans)
                        if spans else 12
                    )
                    is_heading = avg_size >= 14 or (
                        len(line_text) < 80 and line_text.isupper()
                    )

                    if is_heading:
                        page_lines.append(f"\n## {line_text}\n")
                    else:
                        page_lines.append(line_text)

            pages.append("\n".join(page_lines))

        doc.close()
        return "\n\n".join(pages)


# ── Factory ──────────────────────────────────────────────────────────────────

_PARSERS: dict[str, BaseParser] = {
    "text/plain": TxtParser(),
    "text/markdown": MarkdownParser(),
    "application/pdf": PdfParser(),
}


def get_parser(mime_type: str) -> BaseParser:
    parser = _PARSERS.get(mime_type)
    if parser is None:
        supported = ", ".join(_PARSERS.keys())
        raise ValueError(f"Unsupported mime_type '{mime_type}'. Supported: {supported}")
    return parser
