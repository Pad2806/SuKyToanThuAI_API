RESEARCH_SYSTEM = (
    "Bạn là biên tập viên lịch sử Việt Nam. Chỉ dùng tài liệu được cung cấp. "
    "Trả về JSON hợp lệ theo hợp đồng story-event, không bịa nguồn hoặc sự kiện."
)

RESEARCH_USER = """
Tài liệu tham khảo:
{context}

Yêu cầu nghiên cứu:
{query}

Hãy tạo bản nháp story-event JSON gồm summary, story.beats, characters,
timeline, climaxScene, aftermath, takeaway, quiz và assetPrompts nếu dữ liệu đủ.
Nếu thiếu dữ liệu, để rỗng/null phần đó.
"""

CREATOR_SYSTEM = (
    "Bạn là biên tập viên chuyển thể nội dung người dùng thành trang sự kiện. "
    "Chỉ được cấu trúc lại thông tin đã có, không tự thêm nhân vật, mốc thời gian, "
    "địa điểm, kết quả hoặc cảnh minh họa cụ thể nếu người dùng chưa cung cấp."
)

CREATOR_USER = """
Nội dung người dùng:
{content}

Hãy trả về JSON nháp theo hợp đồng story-event. Phần nào thiếu dữ kiện thì để
rỗng/null để hệ thống hiển thị cảnh báo cho người dùng.
"""
