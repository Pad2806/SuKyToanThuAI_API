"""
routers/search.py
Endpoints liên quan đến việc tìm kiếm và đổi ảnh:
  - GET  /api/v1/media/db-check          Kiểm tra kết nối database
  - GET  /api/v1/media/categories        Lấy danh mục sự kiện lịch sử
  - GET  /api/v1/media/search            Tìm ảnh thủ công bằng keyword
  - POST /api/v1/media/regenerate-image  Đổi ảnh khi user không thích
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.schemas.media import RegenerateImageRequestV2, AssetResult
from app.services import wikimedia_service, filter_service, asset_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/media", tags=["Search & Regenerate"])

class KeywordItem(BaseModel):
    keyword_en: str = Field(..., description="Keyword tiếng Anh")
    category: str | None = Field(default=None, description="Loại: location, person, event")


class SearchRequest(BaseModel):
    keywords: list[KeywordItem] = Field(..., min_length=1, description="Danh sách keyword")
    max_results: int = Field(default=10, ge=1, le=30, description="Số ảnh tối đa")
    min_width: int = Field(default=800, description="Chiều rộng tối thiểu (px)")
    license_filter: list[str] = Field(
        default=["cc-by", "cc-by-sa", "public-domain"],
        description="Loại license chấp nhận"
    )


# ── GET /db-check ─────────────────────────────────────────────────────────────

@router.get("/db-check", summary="Kiểm tra kết nối database")
def db_check(db: Session = Depends(get_db)):
    """Dùng để test xem service có kết nối được tới Supabase không."""
    row = db.execute(
        text("""
            SELECT
                current_database() AS database_name,
                current_schema()   AS schema_name,
                NOW()              AS server_time
        """)
    ).mappings().one()

    return {
        "status": "connected",
        "database": row["database_name"],
        "schema": row["schema_name"],
        "server_time": row["server_time"].isoformat(),
    }


# ── GET /categories ───────────────────────────────────────────────────────────

@router.get("/categories", summary="Lấy danh mục sự kiện lịch sử")
def get_categories(
    limit: int = Query(default=20, ge=1, le=100, description="Số lượng danh mục trả về"),
    active_only: bool = Query(default=True, description="Chỉ lấy danh mục đang hiển thị"),
    db: Session = Depends(get_db),
):
    """
    Trả về danh sách danh mục sự kiện lịch sử từ bảng `categories`.
    Dùng để hiển thị menu lọc, hoặc giúp keyword_service biết ngữ cảnh.
    """
    rows = db.execute(
        text("""
            SELECT
                id, slug, name_vi, name_en,
                description_vi, description_en, icon_url,
                parent_id, display_order, is_active,
                created_at, updated_at
            FROM categories
            WHERE (:active_only = FALSE OR is_active = TRUE)
            ORDER BY display_order ASC, created_at DESC
            LIMIT :limit
        """),
        {"limit": limit, "active_only": active_only},
    ).mappings().all()

    return {
        "success": True,
        "count": len(rows),
        "items": [
            {
                "id": str(row["id"]),
                "slug": row["slug"],
                "name_vi": row["name_vi"],
                "name_en": row["name_en"],
                "description_vi": row["description_vi"],
                "description_en": row["description_en"],
                "icon_url": row["icon_url"],
                "parent_id": str(row["parent_id"]) if row["parent_id"] else None,
                "display_order": row["display_order"],
                "is_active": row["is_active"],
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
            }
            for row in rows
        ],
    }


# ── POST /search ───────────────────────────────────────────────────────────────

@router.post("/search", summary="Tìm kiếm ảnh theo keywords")
async def search_images(body: SearchRequest):
    """
    Tìm kiếm ảnh trên Wikimedia Commons theo danh sách keyword tiếng Anh.
    Ảnh đã được lọc theo chất lượng, kích thước và license.
    """
    all_images = []

    for kw_item in body.keywords:
        result = await wikimedia_service.search_images(
            kw_item.keyword_en,
            limit=body.max_results,
        )
        all_images.extend(result.items)

    # Lọc chất lượng
    filtered = filter_service.filter_by_quality(all_images)

    return {
        "success": True,
        "data": {
            "images": [
                {
                    "id": str(item.page_id),
                    "title": item.title,
                    "url": item.image_info.url if item.image_info else None,
                    "thumbnail_url": item.image_info.url if item.image_info else None,
                    "width": item.image_info.width if item.image_info else None,
                    "height": item.image_info.height if item.image_info else None,
                    "license": item.image_info.license_short_name if item.image_info else None,
                    "author": item.image_info.artist if item.image_info else None,
                    "source_url": item.image_info.descriptionurl if item.image_info else None,
                    "relevance_score": None,
                    "matched_keyword": None,
                }
                for item in filtered
            ],
            "total_found": len(filtered),
        },
    }


# ── POST /regenerate-image ─────────────────────────────────────────────────────

@router.post(
    "/regenerate-image",
    summary="Đổi ảnh khi user không hài lòng",
)
async def regenerate_image(body: RegenerateImageRequestV2):
    """
    User bấm 'Đổi ảnh' → FE gọi endpoint này.

    **Nhận vào:**
    - slide_order: slide nào cần đổi ảnh
    - image_suggestion: gợi ý ảnh gốc (từ outline)
    - reason: lý do đổi (optional)
    - preferred_keywords: keyword user muốn tìm (optional)
    - exclude_urls: URL ảnh cũ cần loại bỏ

    **Trả về:**
    - asset: ảnh mới tìm được
    - is_fallback: true nếu không tìm được ảnh thật
    """
    logger.info(
        "regenerate-image: slide_order=%d, reason='%s'",
        body.slide_order,
        body.reason or "không có",
    )

    asset: AssetResult = await asset_service.regenerate_single_slide(body)

    return {
        "success": True,
        "data": {
            "asset": {
                "slide_order": asset.slide_order,
                "image_url": asset.image_url,
                "source": asset.source,
                "license": asset.license,
                "keywords_used": asset.keywords_used,
                "relevance_score": asset.relevance_score,
            },
            "is_fallback": asset.source == "fallback",
        },
    }
