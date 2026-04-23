"""
services/filter_service.py
Thuật toán lọc và chọn ảnh tốt nhất từ kết quả tìm kiếm Wikimedia.

Tiêu chí filter (theo thứ tự ưu tiên):
1. Loại file hợp lệ (JPEG, PNG — không dùng SVG, GIF, WebP)
2. Kích thước đủ lớn (tối thiểu 800x600px)
3. License Creative Commons (không dùng ảnh All Rights Reserved)
4. Relevance score (AI Groq đánh giá mức độ liên quan với scene)

Phase 1: Skeleton + docstring.
Phase 2: Implement đầy đủ và kết nối với Groq để score.
"""
import logging

from app.schemas.wikimedia import WikimediSearchResultItem, WikimediaSearchResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

# Định dạng file được chấp nhận
ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png"}

# License CC được chấp nhận (không phải All Rights Reserved)
ALLOWED_LICENSE_KEYWORDS = {"cc", "creative commons", "public domain", "pd"}


def filter_by_quality(items: list[WikimediSearchResultItem]) -> list[WikimediSearchResultItem]:
    """
    Lọc ảnh theo tiêu chí chất lượng (kích thước + định dạng + license).

    Returns:
        Danh sách ảnh đã qua lọc, chỉ giữ lại ảnh hợp lệ.

    TODO (Phase 2): Implement.
    """
    valid = []
    for item in items:
        info = item.image_info
        if not info:
            continue

        # Kiểm tra định dạng file
        if info.mime not in ALLOWED_MIME_TYPES:
            logger.debug("Bỏ qua ảnh %s: sai định dạng (%s)", item.title, info.mime)
            continue

        # Kiểm tra kích thước tối thiểu
        width = info.width or 0
        height = info.height or 0
        if width < settings.IMAGE_MIN_WIDTH or height < settings.IMAGE_MIN_HEIGHT:
            logger.debug(
                "Bỏ qua ảnh %s: quá nhỏ (%dx%d)", item.title, width, height
            )
            continue

        # Kiểm tra license
        license_name = (info.license_short_name or "").lower()
        is_cc = any(kw in license_name for kw in ALLOWED_LICENSE_KEYWORDS)
        if not is_cc:
            logger.debug("Bỏ qua ảnh %s: không phải CC license (%s)", item.title, license_name)
            continue

        valid.append(item)

    logger.info("Filter quality: %d/%d ảnh hợp lệ", len(valid), len(items))
    return valid


def pick_best_image(
    items: list[WikimediSearchResultItem],
) -> WikimediSearchResultItem | None:
    """
    Chọn ảnh tốt nhất từ danh sách đã qua filter.
    Hiện tại: chọn ảnh đầu tiên (rộng nhất).
    Phase 2: Dùng Groq để score relevance rồi chọn ảnh có score cao nhất.

    Returns:
        Ảnh tốt nhất, hoặc None nếu list rỗng.

    TODO (Phase 2): Kết hợp AI relevance scoring.
    """
    if not items:
        return None

    # Tạm thời: chọn ảnh rộng nhất (thường = chất lượng cao nhất)
    return max(
        items,
        key=lambda item: (item.image_info.width or 0) if item.image_info else 0,
    )
