"""
routers/search.py
Endpoints liên quan đến việc tìm kiếm và đổi ảnh:
  - GET  /api/v1/media/db-check          Kiểm tra kết nối database
  - GET  /api/v1/media/categories        Lấy danh mục sự kiện lịch sử
  - GET  /api/v1/media/search            Tìm ảnh thủ công bằng keyword
  - POST /api/v1/media/regenerate-image  Đổi ảnh khi user không thích
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.media import RegenerateImageRequest, RegenerateImageResponse

router = APIRouter(prefix="/api/v1/media", tags=["Search & Regenerate"])


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


# ── GET /search ───────────────────────────────────────────────────────────────

@router.get("/search", summary="Tìm kiếm ảnh thủ công bằng keyword")
async def search_images(
    keyword: str = Query(..., min_length=2, description="Từ khóa tìm kiếm"),
    limit: int = Query(default=10, ge=1, le=30, description="Số ảnh trả về tối đa"),
):
    """
    Tìm kiếm ảnh trên Wikimedia Commons theo keyword.
    Phase 1: Trả về placeholder — logic thật sẽ được implement ở Phase 2.
    """
    # TODO (Phase 2): Gọi wikimedia_service.search(keyword, limit)
    return {
        "success": True,
        "keyword": keyword,
        "note": "Tính năng search sẽ được implement ở Phase 2",
        "items": [],
    }


# ── POST /regenerate-image ─────────────────────────────────────────────────────

@router.post(
    "/regenerate-image",
    summary="Đổi ảnh khi user không hài lòng",
    response_model=RegenerateImageResponse,
)
async def regenerate_image(body: RegenerateImageRequest):
    """
    User bấm 'Đổi ảnh' → FE gọi endpoint này.
    Phase 1: Trả về stub response — logic thật ở Phase 4.
    """
    # TODO (Phase 4): Gọi asset_service.regenerate(body)
    raise HTTPException(
        status_code=501,
        detail="Tính năng regenerate image sẽ được implement ở Phase 4",
    )
