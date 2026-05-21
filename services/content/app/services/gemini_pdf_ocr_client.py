import json
from typing import Any

from common.config.settings import get_settings

OCR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "pages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["page", "text"],
            },
        },
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["pages"],
}

OCR_PROMPT = """
Extract readable Vietnamese textbook text from this PDF.
Return JSON only. Do not summarize, rewrite, or add facts.
Preserve page order. For each page, return the text visible on that page.
If a page has no readable text, return an empty string for that page.
Do not draft an event page.
"""


class GeminiPdfOcrClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def extract_pages(self, raw: bytes, *, filename: str | None = None) -> dict[str, Any]:
        if self.settings.ai_provider != "vertex":
            raise RuntimeError("Official admin OCR pipeline requires Vertex AI")
        if not self.settings.google_cloud_project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required for Gemini PDF OCR")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("google-genai is not installed") from exc

        client = genai.Client(
            vertexai=True,
            project=self.settings.google_cloud_project,
            location=self.settings.google_cloud_location,
        )
        try:
            response = await client.aio.models.generate_content(
                model=self.settings.ai_fast_model,
                contents=[
                    types.Part.from_text(text=f"{OCR_PROMPT}\nFile name: {filename or 'source.pdf'}"),
                    types.Part.from_bytes(data=raw, mime_type="application/pdf"),
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=OCR_SCHEMA,
                ),
            )
        except Exception as exc:
            raise RuntimeError(_format_ocr_error(exc)) from exc
        try:
            return json.loads(response.text or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("Gemini OCR returned invalid JSON") from exc

def _format_ocr_error(exc: Exception) -> str:
    message = str(exc)
    if "BILLING_DISABLED" in message or "requires billing to be enabled" in message:
        return (
            "Gemini PDF OCR chưa chạy được vì Google Cloud project chưa bật billing "
            "cho Vertex AI. Hãy bật billing cho project hoặc dùng PDF có text, TXT, "
            "hoặc dán nội dung trích dẫn thủ công."
        )
    if "PERMISSION_DENIED" in message:
        return (
            "Gemini PDF OCR bị từ chối quyền truy cập Vertex AI. Hãy kiểm tra billing, "
            "project, location và quyền service account trước khi thử lại."
        )
    return f"Gemini PDF OCR failed: {message}"
