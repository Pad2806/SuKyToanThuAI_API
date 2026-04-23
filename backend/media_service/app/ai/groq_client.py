"""
ai/groq_client.py
Module khởi tạo và cung cấp Groq LLM client.

Tất cả code cần gọi AI (ví dụ: sinh keyword, đánh giá ảnh)
đều import `groq_client` từ file này, KHÔNG tự tạo client mới.
Điều này đảm bảo dùng chung 1 API key và dễ quản lý.
"""
from groq import Groq

from app.core.config import settings

# Singleton Groq client — khởi tạo 1 lần khi service start
# Tất cả service khác import biến này để dùng
groq_client = Groq(api_key=settings.GROQ_API_KEY)

__all__ = ["groq_client"]
