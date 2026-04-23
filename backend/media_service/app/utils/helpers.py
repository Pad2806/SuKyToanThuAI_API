"""
utils/helpers.py
Các hàm tiện ích nhỏ dùng chung trong toàn Media Service.
Không chứa business logic — chỉ là helper thuần túy.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    """
    Chuyển chuỗi tiếng Việt (có dấu) thành slug URL-friendly không dấu.

    Ví dụ:
        "Chiến dịch Điện Biên Phủ" → "chien-dich-dien-bien-phu"
    """
    # Normalize unicode (NFD) rồi encode ASCII để bỏ dấu
    text = unicodedata.normalize("NFD", text.lower())
    text = text.encode("ascii", "ignore").decode("ascii")
    # Thay ký tự đặc biệt bằng dấu gạch ngang
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def strip_html_tags(text: str) -> str:
    """
    Xóa toàn bộ HTML tags trong chuỗi.
    Dùng để làm sạch image_description từ Wikimedia (hay có HTML).

    Ví dụ:
        "<b>Chiến thắng</b> lịch sử" → "Chiến thắng lịch sử"
    """
    return re.sub(r"<[^>]+>", "", text).strip()


def truncate(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Cắt ngắn chuỗi nếu quá dài — dùng để log và hiển thị.

    Ví dụ:
        truncate("Một đoạn văn rất dài...", max_length=20) → "Một đoạn văn rất d..."
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def build_wikimedia_thumbnail_url(original_url: str, width: int = 1200) -> str:
    """
    Chuyển đổi URL ảnh Wikimedia gốc thành URL thumbnail đúng kích thước.
    Wikimedia hỗ trợ resize-on-fly qua URL pattern đặc biệt.

    Ví dụ:
        .../File:image.jpg → .../thumb/.../1200px-image.jpg
    """
    # Nếu đã là thumbnail URL thì trả về luôn
    if "/thumb/" in original_url:
        return original_url

    # Pattern Wikimedia: /wikipedia/commons/a/ab/File.jpg
    # → /wikipedia/commons/thumb/a/ab/File.jpg/{width}px-File.jpg
    match = re.search(r"(/commons/)([a-f0-9]/[a-f0-9]{2}/)(.+)$", original_url)
    if not match:
        return original_url  # Không nhận ra pattern → trả về URL gốc

    prefix, path, filename = match.groups()
    return f"https://upload.wikimedia.org{prefix}thumb/{path}{filename}/{width}px-{filename}"
