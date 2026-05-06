"""
routers/infographic.py
Endpoint riêng cho Infographic — chỉ trả 2 ảnh (header + intro).
  - POST /api/v1/media/infographic-images

Nhận 2 keyword (header_keyword + intro_keyword) từ blocks → search Wikimedia → trả 2 ảnh.
Nếu không có keyword → fallback dùng title để AI sinh keyword.
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import keyword_service, wikimedia_service, filter_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/media", tags=["Infographic"])

FALLBACK_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Example.jpg/1200px-Example.jpg"


# ── Request / Response ────────────────────────────────────────────────────────

class InfographicImagesRequest(BaseModel):
    """Body JSON cho POST /api/v1/media/infographic-images."""
    title: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Tiêu đề sự kiện lịch sử (tiếng Việt). Dùng fallback khi không có keyword.",
    )
    header_keyword: str | None = Field(
        default=None,
        max_length=300,
        description="Keyword tiếng Anh cho ảnh header (từ block header.image_suggestion).",
    )
    intro_keyword: str | None = Field(
        default=None,
        max_length=300,
        description="Keyword tiếng Anh cho ảnh intro (từ block intro.image_suggestion).",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Chiến thắng Điện Biên Phủ 1954",
                "header_keyword": "Dien Bien Phu battle 1954 panorama",
                "intro_keyword": "Dien Bien Phu victory painting illustration",
            }
        }
    }


class InfographicImageItem(BaseModel):
    role: str = Field(..., description="Vai trò: 'header' hoặc 'intro'")
    image_url: str = Field(..., description="URL ảnh Wikimedia")
    source: str = Field(default="wikimedia", description="Nguồn: wikimedia hoặc fallback")
    license: str | None = Field(default=None, description="License ảnh")
    keywords_used: list[str] = Field(default_factory=list, description="Keywords đã dùng")


class InfographicImagesResponse(BaseModel):
    success: bool = True
    data: dict = Field(..., description="{ images: [], total_found: int }")


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "/infographic-images",
    summary="Tìm 2 ảnh cho infographic (header + intro)",
    response_model=InfographicImagesResponse,
    status_code=200,
)
async def get_infographic_images(body: InfographicImagesRequest):
    """
    Endpoint nhẹ cho Infographic — chỉ tìm 2 ảnh.

    **Luồng:**
    1. Nhận header_keyword + intro_keyword (tiếng Anh) từ block.image_suggestion
    2. Nếu không có keyword → dùng AI sinh từ title
    3. Search Wikimedia Commons với từng keyword
    4. Trả 2 ảnh chất lượng cao nhất (khác nhau)

    **Ảnh 1 (header):** Ảnh toàn cảnh / panorama — dùng làm nền hero
    **Ảnh 2 (intro):** Ảnh minh họa / tranh vẽ — dùng cho block giới thiệu
    """
    logger.info(
        "infographic-images: title='%s', header_kw='%s', intro_kw='%s'",
        body.title, body.header_keyword, body.intro_keyword,
    )

    # ── Chuẩn bị keywords ─────────────────────────────────────────────
    header_keywords = await _resolve_keywords(
        body.header_keyword,
        fallback_suggestion=f"{body.title} - ảnh toàn cảnh, bối cảnh lịch sử",
    )
    intro_keywords = await _resolve_keywords(
        body.intro_keyword,
        fallback_suggestion=f"{body.title} - tranh vẽ, chân dung, minh họa lịch sử",
    )

    # ── Tìm ảnh header ────────────────────────────────────────────────
    header_image = await _search_best_image(header_keywords, exclude_urls=[])

    # ── Tìm ảnh intro (loại trừ ảnh header để không trùng) ───────────
    exclude = [header_image["image_url"]] if header_image["source"] != "fallback" else []
    intro_image = await _search_best_image(intro_keywords, exclude_urls=exclude)

    # ── Gán role ──────────────────────────────────────────────────────
    header_image["role"] = "header"
    intro_image["role"] = "intro"

    images = [header_image, intro_image]
    total_found = sum(1 for img in images if img["source"] != "fallback")

    logger.info("infographic-images: tìm được %d/2 ảnh thật", total_found)

    return {
        "success": True,
        "data": {
            "images": images,
            "total_found": total_found,
        },
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _resolve_keywords(
    direct_keyword: str | None,
    fallback_suggestion: str,
) -> list[str]:
    """
    Nếu có keyword trực tiếp (từ block.image_suggestion) → dùng luôn.
    Nếu không → gọi AI sinh keyword từ fallback_suggestion.
    """
    if direct_keyword and direct_keyword.strip():
        # Keyword đã có sẵn từ Gemini → dùng trực tiếp, không cần AI sinh thêm
        return [direct_keyword.strip()]

    # Fallback: gọi AI sinh keyword
    try:
        return await keyword_service.generate_keywords(fallback_suggestion)
    except Exception as e:
        logger.warning("Keyword generation lỗi: %s, dùng fallback text", e)
        return [fallback_suggestion]


async def _search_best_image(
    keywords: list[str],
    exclude_urls: list[str],
) -> dict:
    """Tìm 1 ảnh tốt nhất từ list keywords, loại trừ URLs đã dùng."""
    for kw in keywords:
        try:
            result = await wikimedia_service.search_images(kw, limit=8)
            filtered = filter_service.filter_by_quality(result.items)

            # Loại trừ ảnh đã dùng
            if exclude_urls:
                filtered = [
                    item for item in filtered
                    if item.image_info and item.image_info.url not in exclude_urls
                ]

            best = filter_service.pick_best_image(filtered)

            if best and best.image_info:
                return {
                    "image_url": best.image_info.url,
                    "source": "wikimedia",
                    "license": best.image_info.license_short_name,
                    "keywords_used": keywords,
                }
        except Exception as e:
            logger.warning("Search '%s' lỗi: %s", kw, e)
            continue

    # Fallback
    return {
        "image_url": FALLBACK_IMAGE,
        "source": "fallback",
        "license": None,
        "keywords_used": keywords,
    }
