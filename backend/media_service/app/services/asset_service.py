"""
services/asset_service.py
Orchestrator chính của Media Service — điều phối toàn bộ luồng:
  Scene input → Keyword AI → Wikimedia Search → Filter → Best image

Phase 1: Skeleton + docstring.
Phase 3: Implement đầy đủ.
"""
import logging

from app.schemas.media import (
    GenerateAssetsRequest,
    GenerateAssetsResponse,
    ImageResult,
    ImageSource,
    RegenerateImageRequest,
    RegenerateImageResponse,
    SceneInput,
)

logger = logging.getLogger(__name__)


async def generate_assets(request: GenerateAssetsRequest) -> GenerateAssetsResponse:
    """
    Hàm chính: nhận danh sách scenes, trả về danh sách ảnh.

    Luồng xử lý (Phase 3 implement):
    1. Với mỗi scene:
       a. keyword_service.generate(scene) → keywords[]
       b. Với mỗi keyword: wikimedia_service.search(keyword) → raw_images[]
       c. filter_service.filter_by_quality(raw_images) → filtered[]
       d. filter_service.pick_best_image(filtered) → best_image
    2. Gom kết quả lại và trả về GenerateAssetsResponse

    TODO (Phase 3): Implement.
    """
    logger.info(
        "[Phase 1 Stub] generate_assets: project_type=%s, scenes=%d",
        request.project_type,
        len(request.scenes),
    )
    # Stub: trả về placeholder cho mỗi scene
    images = [
        _make_fallback_image(scene)
        for scene in sorted(request.scenes, key=lambda s: s.order)
    ]
    return GenerateAssetsResponse(
        success=True,
        status="partial",
        images=images,
        fallback_used=True,
        total_scenes=len(request.scenes),
        matched_scenes=0,
    )


async def regenerate_single_image(request: RegenerateImageRequest) -> RegenerateImageResponse:
    """
    Tìm ảnh mới cho 1 scene cụ thể khi user không hài lòng.

    Luồng xử lý (Phase 4 implement):
    1. Dùng preferred_keywords nếu user cung cấp, không thì dùng lại original_scene
    2. Loại bỏ exclude_urls khỏi kết quả search
    3. Tìm và chọn ảnh khác

    TODO (Phase 4): Implement.
    """
    logger.info("[Phase 1 Stub] regenerate_single_image: scene_order=%d", request.scene_order)
    raise NotImplementedError("Implement ở Phase 4")


def _make_fallback_image(scene: SceneInput) -> ImageResult:
    """Tạo ảnh placeholder khi không tìm được ảnh thật."""
    return ImageResult(
        scene_order=scene.order,
        image_url="https://via.placeholder.com/1200x800?text=No+Image+Found",
        image_source=ImageSource.fallback,
        image_title=f"Placeholder — {scene.title}",
        image_license="N/A",
        search_keywords_used=[],
        relevance_score=0.0,
        width=1200,
        height=800,
    )
