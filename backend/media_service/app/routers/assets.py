"""
routers/assets.py
Endpoint chính của Media Service:
  - POST /api/v1/media/generate-assets

Đây là API mà Content Service (Người 2) sẽ gọi sau khi tạo xong outline.
Phase 1: Validate request và trả về stub response đúng schema.
Phase 3: Sẽ implement logic thật.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.schemas.media import GenerateAssetsRequest, GenerateAssetsResponse, ImageResult, ImageSource

router = APIRouter(prefix="/api/v1/media", tags=["Generate Assets"])


@router.post(
    "/generate-assets",
    summary="Tạo hình ảnh cho tất cả các slide/panel",
    response_model=GenerateAssetsResponse,
    status_code=202,  # 202 Accepted — vì có thể xử lý async sau
)
async def generate_assets(
    body: GenerateAssetsRequest,
    background_tasks: BackgroundTasks,
):
    """
    API chính của Media Service.

    **Nhận vào (từ Content Service):**
    - Danh sách scenes (mỗi scene là 1 slide hoặc 1 panel comic)
    - Cấu hình phong cách (academic/dramatic, màu sắc...)

    **Trả về:**
    - Danh sách image_url tương ứng cho từng scene
    - Score relevance để FE hiển thị chất lượng ảnh

    **Luồng xử lý (sẽ implement ở Phase 3):**
    1. Groq LLM → sinh keyword tiếng Anh cho từng scene
    2. Wikimedia Commons → tìm ảnh theo keyword
    3. Filter → loại ảnh nhỏ, sai license, không liên quan
    4. Rank → chọn ảnh phù hợp nhất theo context

    **Phase 1:** Validate schema + trả về stub response đúng format.
    """
    # Validate: phải có ít nhất 1 scene
    if not body.scenes:
        raise HTTPException(status_code=422, detail="Cần ít nhất 1 scene để tạo ảnh")

    # TODO (Phase 3): Gọi asset_service.generate(body)
    # Hiện tại: trả về stub response đúng schema để FE/team có thể test tích hợp trước

    stub_images = [
        ImageResult(
            scene_order=scene.order,
            image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/placeholder.jpg",
            image_source=ImageSource.fallback,
            image_title=f"[Stub] Ảnh cho scene {scene.order}: {scene.title}",
            image_license="CC-BY-SA-4.0",
            search_keywords_used=[scene.title],
            relevance_score=0.0,
            width=1200,
            height=800,
        )
        for scene in sorted(body.scenes, key=lambda s: s.order)
    ]

    return GenerateAssetsResponse(
        success=True,
        status="partial",   # partial vì đang dùng stub
        images=stub_images,
        fallback_used=True,
        total_scenes=len(body.scenes),
        matched_scenes=0,   # Phase 3 sẽ tìm ảnh thật, con số này sẽ tăng
    )
