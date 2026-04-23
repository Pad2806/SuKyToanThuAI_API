"""
schemas/media.py
Định nghĩa cấu trúc dữ liệu (Pydantic) cho request và response
của các API endpoint chính trong Media Service.

Tất cả JSON body gửi vào và trả ra đều phải khớp với các class này.
FastAPI tự động validate và trả lỗi 422 nếu sai format.
"""
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


# ── Enums ─────────────────────────────────────────────────────────────────────

class ProjectType(str, Enum):
    """Loại project: slide thuyết trình hoặc truyện tranh."""
    slide = "slide"
    comic = "comic"


class ImageSource(str, Enum):
    """Nguồn gốc của ảnh trả về."""
    wikimedia = "wikimedia"   # Tìm từ Wikimedia Commons
    fallback = "fallback"     # Ảnh placeholder khi không tìm được


class Mood(str, Enum):
    """Cảm xúc/không khí của từng scene — dùng để tìm ảnh phù hợp."""
    epic = "epic"           # Hùng tráng, hoành tráng
    dramatic = "dramatic"   # Căng thẳng, kịch tính
    tension = "tension"     # Căng thẳng trước trận đánh
    peaceful = "peaceful"   # Bình yên, hòa bình
    tragic = "tragic"       # Bi thương
    neutral = "neutral"     # Trung tính, minh họa


# ── Sub-models (dùng bên trong request/response lớn) ─────────────────────────

class SceneInput(BaseModel):
    """
    Mô tả 1 scene/slide cần tìm ảnh.
    Content Service sẽ gửi danh sách các scene này sang Media Service.
    """
    order: int = Field(..., ge=1, description="Thứ tự của scene (bắt đầu từ 1)")
    title: str = Field(..., min_length=1, max_length=500, description="Tiêu đề slide/chapter")
    content: str = Field(..., min_length=1, description="Nội dung mô tả scene")
    mood: Mood = Field(default=Mood.neutral, description="Cảm xúc/không khí scene")
    characters: list[str] = Field(
        default_factory=list,
        description="Danh sách nhân vật xuất hiện trong scene"
    )
    historical_year: int | None = Field(
        default=None,
        description="Năm lịch sử của scene (dùng để tìm ảnh chính xác hơn)"
    )
    location: str | None = Field(
        default=None,
        description="Địa điểm xảy ra sự kiện (vd: 'Điện Biên Phủ')"
    )


class StyleConfig(BaseModel):
    """Cấu hình phong cách cho toàn bộ project."""
    tone: Literal["academic", "storytelling", "dramatic", "simple"] = "academic"
    art_style: Literal["realistic", "manga", "cartoon", "watercolor"] | None = None
    color_mode: Literal["full_color", "black_white", "sepia"] = "full_color"
    target_audience: Literal["primary", "high_school", "university", "general"] = "high_school"


class ImageResult(BaseModel):
    """Kết quả 1 ảnh tìm được cho 1 scene."""
    scene_order: int = Field(..., description="Scene thứ mấy trong danh sách")
    image_url: str = Field(..., description="URL trực tiếp đến file ảnh")
    image_source: ImageSource = Field(..., description="Nguồn ảnh")
    image_title: str | None = Field(default=None, description="Tên/tiêu đề ảnh gốc")
    image_license: str | None = Field(default=None, description="Giấy phép (vd: CC-BY-SA-4.0)")
    search_keywords_used: list[str] = Field(
        default_factory=list,
        description="Các keyword đã dùng để tìm được ảnh này"
    )
    relevance_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Điểm liên quan (0-1). AI đánh giá ảnh có phù hợp với scene không"
    )
    width: int | None = Field(default=None, description="Chiều rộng ảnh (px)")
    height: int | None = Field(default=None, description="Chiều cao ảnh (px)")


# ── Main Request/Response Schemas ─────────────────────────────────────────────

class GenerateAssetsRequest(BaseModel):
    """
    Body JSON cho POST /api/v1/media/generate-assets
    Content Service gọi API này sau khi đã tạo xong outline.
    """
    project_type: ProjectType = Field(..., description="Loại project: slide hoặc comic")
    scenes: list[SceneInput] = Field(
        ...,
        min_length=1,
        description="Danh sách scene cần tìm ảnh (ít nhất 1 scene)"
    )
    style: StyleConfig = Field(
        default_factory=StyleConfig,
        description="Cấu hình phong cách ảnh"
    )
    language: Literal["vi", "en"] = Field(
        default="vi",
        description="Ngôn ngữ của nội dung (ảnh hưởng tới keyword tìm kiếm)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "project_type": "slide",
                "scenes": [
                    {
                        "order": 1,
                        "title": "Bối cảnh Điện Biên Phủ",
                        "content": "Năm 1954, quân Pháp xây dựng cứ điểm tại thung lũng...",
                        "mood": "tension",
                        "characters": ["Võ Nguyên Giáp", "de Castries"],
                        "historical_year": 1954,
                        "location": "Điện Biên Phủ"
                    }
                ],
                "style": {"tone": "academic"},
                "language": "vi"
            }
        }
    }


class GenerateAssetsResponse(BaseModel):
    """Response trả về sau khi generate xong ảnh cho tất cả scenes."""
    success: bool = True
    status: Literal["completed", "partial", "failed"] = "completed"
    images: list[ImageResult] = Field(..., description="Danh sách ảnh theo thứ tự scene")
    fallback_used: bool = Field(
        default=False,
        description="True nếu có ít nhất 1 scene phải dùng ảnh placeholder"
    )
    total_scenes: int = Field(..., description="Tổng số scene yêu cầu")
    matched_scenes: int = Field(..., description="Số scene tìm được ảnh thật")


class RegenerateImageRequest(BaseModel):
    """
    Body JSON cho POST /api/v1/media/regenerate-image
    FE gọi khi user bấm nút 'Đổi ảnh khác'.
    """
    scene_order: int = Field(..., ge=1, description="Scene thứ mấy cần đổi ảnh")
    reason: str | None = Field(
        default=None,
        max_length=500,
        description="Lý do user muốn đổi ảnh (dùng để tìm ảnh khác ý hơn)"
    )
    preferred_keywords: list[str] = Field(
        default_factory=list,
        description="Keyword user muốn tìm (nếu có)"
    )
    exclude_urls: list[str] = Field(
        default_factory=list,
        description="Danh sách URL ảnh cũ cần loại bỏ, không dùng lại"
    )
    original_scene: SceneInput | None = Field(
        default=None,
        description="Thông tin scene gốc để tìm ảnh lại từ đầu nếu cần"
    )


class RegenerateImageResponse(BaseModel):
    """Response sau khi regenerate thành công."""
    success: bool = True
    image: ImageResult = Field(..., description="Ảnh mới tìm được")
    attempts_made: int = Field(
        default=1,
        description="Số lần thử (retry) trước khi tìm được ảnh"
    )
