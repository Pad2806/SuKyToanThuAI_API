"""
services/asset_service.py
Orchestrator — tìm ảnh minh họa nhỏ từ Wikimedia cho mỗi slide.
FE sẽ render slide bằng HTML/CSS template, ảnh Wikimedia chỉ là minh họa phụ.
"""
import logging

from app.services import keyword_service, wikimedia_service, filter_service
from app.schemas.media import SlideAssetInput, AssetResult, RegenerateImageRequestV2

logger = logging.getLogger(__name__)

FALLBACK_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Example.jpg/1200px-Example.jpg"


async def generate_assets_for_slides(
    slides: list[SlideAssetInput],
) -> list[AssetResult]:
    """Tìm ảnh minh họa Wikimedia cho mỗi slide."""
    results: list[AssetResult] = []

    for slide in sorted(slides, key=lambda s: s.slide_order):
        logger.info("Slide %d: '%s'", slide.slide_order, slide.image_suggestion)
        asset = await _find_illustration(slide)
        results.append(asset)

    return results


async def _find_illustration(slide: SlideAssetInput) -> AssetResult:
    """Tìm 1 ảnh minh họa nhỏ cho slide từ Wikimedia."""
    keywords = []

    # Sinh keyword EN
    try:
        keywords = await keyword_service.generate_keywords(slide.image_suggestion)
    except Exception as e:
        logger.warning("  Keyword lỗi: %s", e)
        keywords = [slide.image_suggestion]

    # Search Wikimedia
    for kw in keywords:
        try:
            result = await wikimedia_service.search_images(kw, limit=5)
            filtered = filter_service.filter_by_quality(result.items)
            best = filter_service.pick_best_image(filtered)

            if best and best.image_info:
                return AssetResult(
                    slide_order=slide.slide_order,
                    image_url=best.image_info.url,
                    source="wikimedia",
                    license=best.image_info.license_short_name,
                    keywords_used=keywords,
                    relevance_score=None,
                )
        except Exception as e:
            logger.warning("  Search '%s' lỗi: %s", kw, e)
            continue

    # Fallback
    return AssetResult(
        slide_order=slide.slide_order,
        image_url=FALLBACK_IMAGE,
        source="fallback",
        license=None,
        keywords_used=keywords,
        relevance_score=0.0,
    )


async def regenerate_single_slide(request: RegenerateImageRequestV2) -> AssetResult:
    """Tìm ảnh minh họa mới."""
    slide = SlideAssetInput(
        slide_order=request.slide_order,
        image_suggestion=request.image_suggestion,
    )
    return await _find_illustration(slide)
