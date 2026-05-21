from pydantic import BaseModel, Field


class CreatorRequest(BaseModel):
    content: str = Field(min_length=1, max_length=12000)
    template: str = "universal"

class Character(BaseModel):
    id: str = Field(description="Slug id của nhân vật (viết liền không dấu, VD: ho-chi-minh)")
    name: str
    role: str = Field(description="Vai trò (vd: Nhân vật, Lãnh đạo, Tướng...)")
    side: str = Field(default="other", description="Phe phái viết thường không dấu (vd: viet-minh, phap, my, other...)")
    side_type: str = Field(default="neutral", description="Phân loại phe phái: 'ally' (phe ta/Việt Nam/Đồng minh), 'enemy' (đối phương/xâm lược/địch), hoặc 'neutral' (trung lập/khác)")
    side_name: str = Field(default="", description="Tên hiển thị đầy đủ của phe phái trong tiếng Việt (VD: Đại Việt, Thực dân Pháp, Nhà Minh, Quân Nam Hán...)")
    portrait: str | None = None
    bio: str
    quote: str | None = None


class TimelineEvent(BaseModel):
    id: str = Field(description="Mã event, vd: m1, m2...")
    year: str = Field(description="Năm xảy ra sự kiện")
    month: str = Field(default="", description="Tháng xảy ra (nếu có)")
    title: str = Field(description="Tiêu đề sự kiện (ngắn gọn)")
    description: str = Field(description="Mô tả chi tiết")

class ClimaxPhase(BaseModel):
    id: str = Field(description="Mã phase, vd: p1, p2, p3...")
    label: str = Field(description="Tên giai đoạn cao trào (VD: Chuẩn bị: Đóng cọc ngầm)")
    summary: str = Field(description="Tóm tắt ngắn gọn của giai đoạn (dưới 120 ký tự)")
    description: str = Field(description="Chi tiết diễn biến giai đoạn cao trào này")
    key_detail: str | None = Field(default=None, description="Chi tiết đắt giá hoặc điểm mấu chốt của giai đoạn")

class ClimaxHotspot(BaseModel):
    id: str = Field(description="Mã hotspot, vd: hs1, hs2...")
    x: int = Field(description="Toạ độ x phần trăm trên bản đồ/ảnh cao trào (0-100)")
    y: int = Field(description="Toạ độ y phần trăm trên bản đồ/ảnh cao trào (0-100)")
    label: str = Field(description="Nhãn hiển thị khi tương tác")
    description: str = Field(description="Mô tả cụ thể của điểm nóng này")

class ClimaxSceneData(BaseModel):
    title: str = Field(description="Tiêu đề của cảnh cao trào, VD: Trận Bạch Đằng 938")
    phases: list[ClimaxPhase] = Field(default_factory=list, description="Danh sách 2-3 giai đoạn nhỏ liên tiếp trong cảnh cao trào để scrollytelling")
    hotspots: list[ClimaxHotspot] = Field(default_factory=list, description="Các điểm tương tác trên bản đồ nếu đây là trận đánh/địa điểm cụ thể, nếu không có thì để trống")

class HistoryEventContent(BaseModel):
    title: str
    summary: str
    sentences: list[str] = Field(default_factory=list)
    year: int | None = None
    location: str | None = None
    characters: list[Character] = Field(default_factory=list)
    actors: list[str] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    climax: ClimaxSceneData | None = Field(default=None, description="Cảnh cao trào trọng tâm của sự kiện (gồm nhiều giai đoạn/phases)")
    aftermath: str | None = None
    result: str | None = None
    image_details: str | None = None
    template: str = "universal" 


