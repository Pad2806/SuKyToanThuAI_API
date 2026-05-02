"""
services/asset_service.py
Orchestrator chính của Media Service — điều phối toàn bộ luồng:
  image_suggestion → Keyword AI → Wikimedia Search → Filter → Best image

Phase 3: Implement đầy đủ.
"""
import logging

from app.services import keyword_service, wikimedia_service, filter_service
from app.schemas.media import SlideAssetInput, AssetResult, RegenerateImageRequestV2

logger = logging.getLogger(__name__)

# URL placeholder khi không tìm được ảnh
FALLBACK_IMAGE_URL = "https://via.placeholder.com/1200x800?text=No+Image+Found"


async def generate_assets_for_slides(
    slides: list[SlideAssetInput],
) -> list[AssetResult]:
    """
    Hàm chính: nhận danh sách slides, trả về danh sách ảnh.

    Luồng xử lý cho MỖI slide:
    1. keyword_service.generate_keywords(image_suggestion) → keywords[]
    2. Với mỗi keyword: wikimedia_service.search_images(keyword) → raw_images[]
    3. filter_service.filter_by_quality(raw_images) → filtered[]
    4. filter_service.pick_best_image(filtered) → best_image
    5. Nếu không tìm được → trả fallback

    Args:
        slides: Danh sách slide cần tìm ảnh

    Returns:
        Danh sách AssetResult tương ứng với mỗi slide
    """
    results: list[AssetResult] = []

    for slide in sorted(slides, key=lambda s: s.slide_order):
        logger.info(
            "Đang xử lý slide %d: '%s'",
            slide.slide_order,
            slide.image_suggestion,
        )

        asset = await _process_single_slide(slide)
        results.append(asset)

    return results


async def _process_single_slide(slide: SlideAssetInput) -> AssetResult:
    """
    Xử lý 1 slide: sinh keyword → search → filter → chọn ảnh tốt nhất.

    Chiến lược retry khi không tìm được ảnh:
    1. Lần 1: Dùng keyword AI sinh ra (cụ thể, chính xác)
    2. Lần 2: Dùng keyword rút gọn (bỏ chi tiết, giữ tên sự kiện chính)
    3. Lần 3: Dùng image_suggestion gốc làm keyword (fallback cuối)
    4. Nếu vẫn không có → trả placeholder
    """
    all_keywords_used: list[str] = []

    # ── Bước 1: AI sinh keyword tiếng Anh ─────────────────────────────
    try:
        keywords = await keyword_service.generate_keywords(slide.image_suggestion)
        logger.info("  Keywords: %s", keywords)
    except Exception as e:
        logger.warning("  Lỗi sinh keyword cho slide %d: %s", slide.slide_order, e)
        # Fallback: dùng image_suggestion gốc làm keyword
        keywords = [slide.image_suggestion]

    # ── Bước 2: Search + Filter (có retry) ────────────────────────────
    # Lần 1: Thử tất cả keyword AI sinh ra
    best, used_keywords = await _search_and_filter(keywords)
    all_keywords_used.extend(used_keywords)

    if best:
        return _make_success(slide, best, all_keywords_used)

    # Lần 2: Thử keyword rút gọn (chỉ lấy 2 từ đầu mỗi keyword)
    logger.info("  Retry lần 2: keyword rút gọn cho slide %d", slide.slide_order)
    short_keywords = _shorten_keywords(keywords)
    if short_keywords:
        best, used_keywords = await _search_and_filter(short_keywords)
        all_keywords_used.extend(used_keywords)

        if best:
            return _make_success(slide, best, all_keywords_used)

    # Lần 3: Dùng image_suggestion gốc (tiếng Việt) làm keyword cuối cùng
    logger.info("  Retry lần 3: dùng image_suggestion gốc cho slide %d", slide.slide_order)
    best, used_keywords = await _search_and_filter([slide.image_suggestion])
    all_keywords_used.extend(used_keywords)

    if best:
        return _make_success(slide, best, all_keywords_used)

    # Hết cách → trả fallback
    logger.warning("  ❌ Không tìm được ảnh sau 3 lần thử cho slide %d", slide.slide_order)
    return _make_fallback(slide, keywords_used=all_keywords_used)


async def _search_and_filter(
    keywords: list[str],
) -> tuple["WikimediSearchResultItem | None", list[str]]:
    """
    Search Wikimedia + filter cho danh sách keyword.
    Returns: (best_image hoặc None, danh sách keyword đã dùng)
    """
    from app.schemas.wikimedia import WikimediSearchResultItem

    all_images = []
    used = []

    for kw in keywords:
        try:
            result = await wikimedia_service.search_images(kw, limit=5)
            logger.info("  Search '%s' → %d ảnh", kw, result.total_found)
            all_images.extend(result.items)
            used.append(kw)
        except Exception as e:
            logger.warning("  Lỗi search '%s': %s", kw, e)
            continue

    if not all_images:
        return None, used

    filtered = filter_service.filter_by_quality(all_images)
    logger.info("  Filter: %d/%d ảnh hợp lệ", len(filtered), len(all_images))

    if not filtered:
        return None, used

    best = filter_service.pick_best_image(filtered)
    if not best or not best.image_info:
        return None, used

    return best, used


def _shorten_keywords(keywords: list[str]) -> list[str]:
    """Rút gọn keyword: lấy 2-3 từ đầu, bỏ chi tiết phụ."""
    short = []
    for kw in keywords:
        words = kw.split()
        if len(words) > 3:
            short.append(" ".join(words[:3]))
        # Nếu keyword đã ngắn thì bỏ qua (tránh trùng)
    return list(set(short))  # Loại trùng


def _make_success(slide: SlideAssetInput, best, keywords_used: list[str]) -> AssetResult:
    """Tạo kết quả thành công từ ảnh tìm được."""
    logger.info(
        "  ✅ Slide %d → '%s' (%dx%d)",
        slide.slide_order,
        best.title,
        best.image_info.width or 0,
        best.image_info.height or 0,
    )
    return AssetResult(
        slide_order=slide.slide_order,
        image_url=best.image_info.url,
        source="wikimedia",
        license=best.image_info.license_short_name,
        keywords_used=keywords_used,
        relevance_score=None,
    )


def _make_fallback(
    slide: SlideAssetInput,
    keywords_used: list[str],
) -> AssetResult:
    """Tạo ảnh placeholder khi không tìm được ảnh thật."""
    return AssetResult(
        slide_order=slide.slide_order,
        image_url=FALLBACK_IMAGE_URL,
        source="fallback",
        license=None,
        keywords_used=keywords_used,
        relevance_score=0.0,
    )


async def regenerate_single_slide(
    request: RegenerateImageRequestV2,
) -> AssetResult:
    """
    Tìm ảnh MỚI cho 1 slide khi user không hài lòng.

    Chiến lược:
    1. Nếu user cung cấp preferred_keywords → dùng luôn
    2. Nếu không → AI sinh keyword mới từ image_suggestion + reason
    3. Search Wikimedia, loại bỏ exclude_urls
    4. Chọn ảnh tốt nhất từ kết quả còn lại
    """
    slide = SlideAssetInput(
        slide_order=request.slide_order,
        image_suggestion=request.image_suggestion,
    )
    all_keywords_used: list[str] = []

    # ── Bước 1: Xác định keyword ──────────────────────────────────────
    if request.preferred_keywords:
        keywords = request.preferred_keywords[:5]
        logger.info("  Dùng preferred_keywords: %s", keywords)
    else:
        suggestion = request.image_suggestion
        if request.reason:
            suggestion = f"{suggestion} ({request.reason})"

        try:
            keywords = await keyword_service.generate_keywords(suggestion)
        except Exception as e:
            logger.warning("  Lỗi sinh keyword: %s", e)
            keywords = [request.image_suggestion]

    all_keywords_used.extend(keywords)

    # ── Bước 2: Search + Filter (loại bỏ ảnh cũ) ─────────────────────
    exclude_set = set(request.exclude_urls)

    for kw in keywords:
        try:
            result = await wikimedia_service.search_images(kw, limit=10)
            logger.info("  Search '%s' → %d ảnh", kw, result.total_found)
        except Exception as e:
            logger.warning("  Lỗi search '%s': %s", kw, e)
            continue

        # Lọc chất lượng
        filtered = filter_service.filter_by_quality(result.items)

        # Loại bỏ ảnh cũ (exclude_urls)
        filtered = [
            item for item in filtered
            if item.image_info and item.image_info.url not in exclude_set
        ]

        if not filtered:
            continue

        # Chọn ảnh tốt nhất
        best = filter_service.pick_best_image(filtered)
        if best and best.image_info:
            logger.info(
                "  ✅ Regenerate slide %d → '%s'",
                request.slide_order,
                best.title,
            )
            return AssetResult(
                slide_order=request.slide_order,
                image_url=best.image_info.url,
                source="wikimedia",
                license=best.image_info.license_short_name,
                keywords_used=all_keywords_used,
                relevance_score=None,
            )

    # Hết cách → fallback
    logger.warning("  ❌ Regenerate thất bại cho slide %d", request.slide_order)
    return _make_fallback(slide, keywords_used=all_keywords_used)
