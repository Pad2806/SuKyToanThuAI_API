"""
routers/slides.py
Endpoint sinh file PPTX từ structured slides JSON.
POST /api/v1/media/generate-pptx
"""
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.slide_generator import generate_pptx
from app.services.google_slides_service import create_presentation_with_user_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/media", tags=["Slide Generation"])


class SlideItem(BaseModel):
    slide_order: int = 1
    layout_type: str = "content"
    title: str = ""
    subtitle: str | None = None
    content: str | None = None
    bullets: list[str] | None = None
    columns: list[dict] | None = None
    events: list[dict] | None = None
    table_headers: list[str] | None = None
    table_rows: list[list[str]] | None = None
    footer_text: str | None = None
    quote_text: str | None = None
    quote_author: str | None = None
    quote_context: str | None = None
    image_suggestion: str | None = None


class GeneratePptxRequest(BaseModel):
    title: str = Field(..., description="Tiêu đề bài thuyết trình")
    slides: list[SlideItem] = Field(..., min_length=1, description="Danh sách slides")


@router.post(
    "/generate-pptx",
    summary="Sinh file PPTX từ structured slides JSON",
    response_class=Response,
)
async def generate_pptx_endpoint(body: GeneratePptxRequest):
    """
    Nhận structured slides JSON (từ Content Service outline) → trả file PPTX.

    FE gọi API này → nhận file PPTX → download.
    """
    logger.info("generate-pptx: title='%s', slides=%d", body.title, len(body.slides))

    try:
        slides_data = [s.model_dump() for s in body.slides]
        pptx_bytes = generate_pptx(body.title, slides_data)

        # Filename ASCII-safe cho HTTP header
        import unicodedata
        safe_name = unicodedata.normalize("NFKD", body.title)
        safe_name = safe_name.encode("ascii", "ignore").decode("ascii")
        safe_name = safe_name.replace(" ", "_") or "slide"
        filename = f"{safe_name}.pptx"

        return Response(
            content=pptx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception as e:
        import traceback
        logger.error("Lỗi sinh PPTX: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Lỗi sinh PPTX: {str(e)}")


class GenerateGoogleSlidesRequest(BaseModel):
    title: str = Field(..., description="Tiêu đề bài thuyết trình")
    slides: list[SlideItem] = Field(..., min_length=1)
    google_access_token: str = Field(..., description="Google OAuth2 access token từ FE")


@router.post(
    "/generate-google-slides",
    summary="Tạo Google Slides presentation trong Drive của user",
)
async def generate_google_slides_endpoint(body: GenerateGoogleSlidesRequest):
    """
    Nhận structured slides JSON + Google access token → tạo Google Slides trong Drive của user.
    FE lấy access token qua Google Sign-In → gửi kèm request.
    """
    logger.info("generate-google-slides: title='%s', slides=%d", body.title, len(body.slides))

    try:
        slides_data = [s.model_dump() for s in body.slides]
        result = create_presentation_with_user_token(
            body.google_access_token, body.title, slides_data
        )

        return {
            "success": True,
            "data": result,
        }
    except Exception as e:
        import traceback
        logger.error("Lỗi tạo Google Slides: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Lỗi tạo Google Slides: {str(e)}")
