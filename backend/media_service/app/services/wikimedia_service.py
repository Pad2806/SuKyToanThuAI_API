"""
services/wikimedia_service.py
Module gọi Wikimedia Commons API để tìm ảnh lịch sử.

Phase 1: Skeleton + docstring đầy đủ.
Phase 2: Implement logic thật.

Wikimedia API docs: https://www.mediawiki.org/wiki/API:Main_page
"""
import logging

import httpx

from app.core.config import settings
from app.core.exceptions import WikimediaError
from app.schemas.wikimedia import WikimediaImageInfo, WikimediaSearchResponse, WikimediSearchResultItem

logger = logging.getLogger(__name__)


async def search_images(keyword: str, limit: int = 10) -> WikimediaSearchResponse:
    """
    Tìm kiếm ảnh trên Wikimedia Commons theo keyword.

    Args:
        keyword: Từ khóa tìm kiếm (nên là tiếng Anh)
        limit:   Số kết quả tối đa cần lấy (default 10, max 30)

    Returns:
        WikimediaSearchResponse chứa danh sách ảnh thô (chưa filter)

    Raises:
        WikimediaError: Khi gọi API thất bại hoặc timeout

    TODO (Phase 2): Implement đầy đủ với httpx async call.
    """
    # Tham số gửi tới Wikimedia API
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": keyword,
        "gsrnamespace": 6,        # Namespace 6 = File (ảnh)
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": 1200,       # Lấy thumbnail rộng 1200px
        "format": "json",
        "utf8": 1,
    }

    headers = {
        "User-Agent": settings.WIKIMEDIA_USER_AGENT,
    }

    # TODO (Phase 2): Thay khối dưới đây bằng httpx async call thật
    # async with httpx.AsyncClient(timeout=15.0) as client:
    #     response = await client.get(settings.WIKIMEDIA_API_URL, params=params, headers=headers)
    #     response.raise_for_status()
    #     data = response.json()
    #     return _parse_wikimedia_response(keyword, data)

    logger.info("[Phase 1 Stub] search_images('%s', limit=%d)", keyword, limit)
    return WikimediaSearchResponse(keyword_used=keyword, total_found=0, items=[])


def _parse_wikimedia_response(keyword: str, data: dict) -> WikimediaSearchResponse:
    """
    Parse raw JSON từ Wikimedia API thành WikimediaSearchResponse.
    Wikimedia API có cấu trúc lồng nhau khá phức tạp nên tách ra hàm riêng.

    TODO (Phase 2): Implement.
    """
    pages = data.get("query", {}).get("pages", {})
    items: list[WikimediSearchResultItem] = []

    for page_id_str, page_data in pages.items():
        image_infos = page_data.get("imageinfo", [])
        if not image_infos:
            continue

        raw_info = image_infos[0]
        ext_meta = raw_info.get("extmetadata", {})

        info = WikimediaImageInfo(
            url=raw_info.get("url", ""),
            descriptionurl=raw_info.get("descriptionurl"),
            mime=raw_info.get("mime"),
            width=raw_info.get("width"),
            height=raw_info.get("height"),
            size=raw_info.get("size"),
            license_short_name=ext_meta.get("LicenseShortName", {}).get("value"),
            image_description=ext_meta.get("ImageDescription", {}).get("value"),
            artist=ext_meta.get("Artist", {}).get("value"),
            date_time=ext_meta.get("DateTime", {}).get("value"),
        )

        items.append(WikimediSearchResultItem(
            page_id=int(page_id_str),
            title=page_data.get("title", ""),
            image_info=info,
        ))

    return WikimediaSearchResponse(
        keyword_used=keyword,
        total_found=len(items),
        items=items,
    )
