"""
routers/assets.py
Endpoint chính của Media Service:
  - POST /api/v1/media/generate-assets

FE gọi API này sau khi có outline từ Content Service.
Phase 3: Implement logic thật.
"""
import logging

from fastapi import APIRouter, HTTPException

from app.schemas.media import (
    GenerateAssetsRequestV2,
    AssetResult,
)
from app.services import asset_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/media", tags=["Generate Assets"])


@router.post(
    "/generate-assets",
    summary="Tạo hình ảnh cho tất cả các slide",
    status_code=200,
)
async def generate_assets(body: GenerateAssetsRequestV2):
    """
    API chính của Media Service.

    **Nhận vào (từ FE, sau khi có outline):**
    - project_id: UUID của project
    - slides[]: danh sách slide, mỗi slide có slide_order + image_suggestion

    **Xử lý:**
    1. Với mỗi slide: AI sinh keyword EN từ image_suggestion
    2. Search Wikimedia Commons bằng keyword EN
    3. Lọc ảnh theo chất lượng (kích thước, license, format)
    4. Chọn ảnh tốt nhất

    **Trả về:**
    - assets[]: danh sách ảnh tương ứng cho từng slide
    - total_matched: số slide tìm được ảnh thật
    - total_requested: tổng số slide yêu cầu
    """
    # Validate
    if not body.slides:
        raise HTTPException(status_code=422, detail="Cần ít nhất 1 slide")

    logger.info(
        "generate-assets: project_id=%s, slides=%d",
        body.project_id,
        len(body.slides),
    )

    # Gọi asset_service xử lý
    assets: list[AssetResult] = await asset_service.generate_assets_for_slides(
        body.slides
    )

    # Đếm số slide tìm được ảnh thật (không phải fallback)
    matched = sum(1 for a in assets if a.source != "fallback")

    return {
        "success": True,
        "data": {
            "assets": [
                {
                    "slide_order": a.slide_order,
                    "image_url": a.image_url,
                    "source": a.source,
                    "license": a.license,
                    "keywords_used": a.keywords_used,
                    "relevance_score": a.relevance_score,
                }
                for a in assets
            ],
            "total_matched": matched,
            "total_requested": len(body.slides),
        },
    }
