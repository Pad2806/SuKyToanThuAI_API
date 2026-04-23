"""
schemas/wikimedia.py
Định nghĩa cấu trúc dữ liệu cho kết quả trả về từ Wikimedia Commons API.
Dùng để parse JSON response trước khi filter và chọn ảnh tốt nhất.
"""
from pydantic import BaseModel, Field


class WikimediaImageInfo(BaseModel):
    """
    Thông tin ảnh từ Wikimedia API (prop=imageinfo&iiprop=url|size|mime|extmetadata).
    Không phải trường nào cũng có — dùng | None để tránh crash.
    """
    url: str = Field(..., description="URL đầy đủ tới file ảnh gốc")
    descriptionurl: str | None = Field(
        default=None, description="URL trang mô tả ảnh trên Wikimedia"
    )
    mime: str | None = Field(default=None, description="Loại file (vd: image/jpeg)")
    width: int | None = Field(default=None, description="Chiều rộng ảnh (px)")
    height: int | None = Field(default=None, description="Chiều cao ảnh (px)")
    size: int | None = Field(default=None, description="Dung lượng file (bytes)")

    # Metadata từ extmetadata (Wikimedia trả về dạng {'value': ..., 'source': ...})
    license_short_name: str | None = Field(
        default=None, description="Tên ngắn giấy phép (vd: CC BY-SA 4.0)"
    )
    image_description: str | None = Field(
        default=None, description="Mô tả ảnh gốc từ Wikimedia"
    )
    artist: str | None = Field(default=None, description="Tác giả/nguồn ảnh")
    date_time: str | None = Field(default=None, description="Ngày chụp/tạo ảnh")


class WikimediSearchResultItem(BaseModel):
    """
    1 kết quả ảnh từ Wikimedia search.
    Wikimedia API trả về dạng: pages[page_id] = {title, imageinfo[...]}
    """
    page_id: int = Field(..., description="ID trang trên Wikimedia")
    title: str = Field(..., description="Tên file (vd: 'File:Battle_of_DBP.jpg')")
    image_info: WikimediaImageInfo | None = Field(
        default=None,
        description="Thông tin chi tiết ảnh (None nếu API không trả về)"
    )


class WikimediaSearchResponse(BaseModel):
    """
    Kết quả parse từ response của Wikimedia search API.
    Sau khi parse sẽ được đẩy vào filter_service để lọc và chọn ảnh tốt nhất.
    """
    keyword_used: str = Field(..., description="Keyword đã dùng để search")
    total_found: int = Field(default=0, description="Tổng số ảnh tìm được")
    items: list[WikimediSearchResultItem] = Field(
        default_factory=list,
        description="Danh sách ảnh tìm được (chưa filter)"
    )
