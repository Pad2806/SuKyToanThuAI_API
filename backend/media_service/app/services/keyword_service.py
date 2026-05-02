"""
services/keyword_service.py
Dùng Groq AI để sinh keyword tiếng Anh từ image_suggestion.

Input:  image_suggestion (tiếng Việt) từ outline của Content Service
Output: list keyword tiếng Anh để search Wikimedia Commons

Ví dụ:
    Input:  "Panorama thung lũng Điện Biên Phủ"
    Output: ["Dien Bien Phu valley panorama 1954", "Battle of Dien Bien Phu aerial view"]
"""
import json
import logging

from app.ai.groq_client import groq_client
from app.core.config import settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)


async def generate_keywords(image_suggestion: str) -> list[str]:
    """
    Nhận image_suggestion (tiếng Việt) → gọi Groq AI → trả về list keyword tiếng Anh.

    Args:
        image_suggestion: Gợi ý ảnh từ outline (VD: "Panorama thung lũng Điện Biên Phủ")

    Returns:
        List 3-5 keyword tiếng Anh. VD: ["Dien Bien Phu valley 1954", ...]

    Raises:
        AIServiceError: Khi Groq API lỗi hoặc không parse được JSON
    """
    prompt = _build_keyword_prompt(image_suggestion)

    try:
        response = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that returns ONLY valid JSON arrays of strings.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
            max_tokens=200,
        )
    except Exception as e:
        logger.error("Groq API lỗi: %s", e)
        raise AIServiceError(f"Không thể gọi Groq AI: {e}")

    raw_text = response.choices[0].message.content.strip()
    logger.info("Groq trả về: %s", raw_text)

    # Parse JSON
    try:
        keywords = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("AI không trả về JSON hợp lệ, thử fallback parse: %s", raw_text)
        keywords = [kw.strip().strip('"') for kw in raw_text.split(",") if kw.strip()]

    # Validate
    keywords = [str(kw).strip() for kw in keywords if kw and str(kw).strip()]
    keywords = keywords[:5]

    if not keywords:
        logger.warning("AI không sinh được keyword, dùng fallback: %s", image_suggestion)
        keywords = [image_suggestion]

    logger.info("Keywords cho '%s': %s", image_suggestion, keywords)
    return keywords


def _build_keyword_prompt(image_suggestion: str) -> str:
    """Tạo prompt yêu cầu AI sinh keyword EN từ image_suggestion tiếng Việt."""
    return f"""You are a historian and image search expert.

Given a Vietnamese image description for a historical slide/comic, generate 3-5 precise
English search keywords suitable for finding relevant images on Wikimedia Commons.

Image description (Vietnamese): {image_suggestion}

Rules:
1. Keywords MUST be in English (Wikimedia Commons is primarily English)
2. Be SPECIFIC — include year, event name, person names when possible
3. Avoid overly generic terms like "war", "history", "battle"
4. Each keyword should be a searchable phrase (2-5 words)
5. Return ONLY a JSON array of strings, nothing else

Example:
  Input: "Panorama thung lũng Điện Biên Phủ"
  Output: ["Dien Bien Phu valley panorama 1954", "Battle of Dien Bien Phu aerial view"]

Your keywords:"""