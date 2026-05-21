import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)


INTENT_SYSTEM = """Bạn là bộ phân tích truy vấn lịch sử Việt Nam.
Nhiệm vụ: Nhận câu truy vấn của người dùng, trả về JSON chứa tham số tìm kiếm.

Trả về JSON (KHÔNG markdown):
{
  "keywords": ["danh sách từ khoá lịch sử cần tìm - tên sự kiện, nhân vật, địa danh, triều đại"],
  "grade_filter": "4" | "5" | ... | "12" | "TH" | "THCS" | "THPT" | null,
  "year_terms": ["các năm hoặc thế kỷ liên quan"],
  "search_strategy": "specific_event" | "broad_topic" | "grade_based" | "time_period"
}

─── BẢNG QUY ĐỔI TÊN THỜI KỲ ───
Khi user nhắc đến TÊN thời kỳ, hãy dùng bảng này để quy đổi ra year_terms:
- "cổ đại" / "thời dựng nước"  → khoảng 2879 TCN – 179 TCN (Hùng Vương, An Dương Vương)
- "Bắc thuộc"                  → 179 TCN – 938 (1000 năm đô hộ phương Bắc)
- "phong kiến" / "trung đại"   → 939 – 1858 (từ Ngô Quyền đến khi Pháp xâm lược)
- "cận đại"                    → 1858 – 1945 (Pháp thuộc, kháng chiến chống Pháp)
- "hiện đại"                   → 1945 – nay (từ Cách mạng tháng Tám đến nay)
- "cận hiện đại"               → 1858 – nay (cận đại + hiện đại)

QUY TẮC NĂM:
- Năm trước Công nguyên: ghi dạng "2879 TCN", "179 TCN" (KHÔNG dùng số âm)
- Năm sau Công nguyên: ghi bình thường "938", "1945"
- "thế kỷ 19" → ["1800", "1900", "thế kỷ 19"]
- "năm 1945" → ["1945"]

Quy tắc:
- keywords: CHỈ trích từ khoá lịch sử thực sự. Loại bỏ noise: "tạo trang", "tóm tắt", "cho tôi", "viết về"...
- grade_filter (QUAN TRỌNG — phân biệt lớp cụ thể và cấp học chung):
  - Nếu user nói RÕ SỐ LỚP (VD: "lớp 12", "lớp 6") → trả SỐ LỚP dạng string: "12", "6", "4"...
  - Nếu user nói CẤP HỌC CHUNG (VD: "THPT", "trung học phổ thông") → trả mã cấp: "TH", "THCS", "THPT"
  - Nếu không đề cập → null
- search_strategy (QUAN TRỌNG, LUÔN ƯU TIÊN):
  - "time_period": Nếu câu hỏi đề cập đến một khoảng thời gian dài, mốc thời gian, nhiều thế kỷ, hoặc TÊN THỜI KỲ (VD: "từ thế kỷ 16 đến 20", "lịch sử hiện đại", "thời phong kiến", "lịch sử cổ đại").
  - "grade_based": hỏi theo lớp học (VD: "lịch sử lớp 12")
  - "specific_event": hỏi về 1 sự kiện/nhân vật cụ thể (VD: "Khởi nghĩa Hai Bà Trưng", "Chiến thắng Bạch Đằng")
  - "broad_topic": hỏi chung về một chủ đề (VD: "các cuộc khởi nghĩa chống Pháp")

Ví dụ:
- "tóm tắt lịch sử cổ đại" → {"keywords":["cổ đại","dựng nước","Hùng Vương","An Dương Vương"],"grade_filter":null,"year_terms":["2879 TCN","179 TCN"],"search_strategy":"time_period"}
- "tóm tắt lịch sử hiện đại" → {"keywords":["hiện đại","kháng chiến","cách mạng"],"grade_filter":null,"year_terms":["1945","1954","1975","2000"],"search_strategy":"time_period"}
- "tóm tắt lịch sử thời phong kiến" → {"keywords":["phong kiến","triều đại"],"grade_filter":null,"year_terms":["939","1009","1225","1400","1428","1802"],"search_strategy":"time_period"}
- "tóm tắt lịch sử từ thế kỉ 16 tới 20" → {"keywords":[],"grade_filter":null,"year_terms":["thế kỷ 16","thế kỷ 17","thế kỷ 18","thế kỷ 19","thế kỷ 20"],"search_strategy":"time_period"}
- "tóm tắt lịch sử thời Bắc thuộc" → {"keywords":["Bắc thuộc","đô hộ"],"grade_filter":null,"year_terms":["179 TCN","938"],"search_strategy":"time_period"}
- "tạo trang Khởi nghĩa Hai Bà Trưng" → {"keywords":["Khởi nghĩa Hai Bà Trưng","Hai Bà Trưng","Trưng Trắc"],"grade_filter":null,"year_terms":["40"],"search_strategy":"specific_event"}
- "tóm tắt lịch sử lớp 12" → {"keywords":[],"grade_filter":"12","year_terms":[],"search_strategy":"grade_based"}
- "lịch sử THPT" → {"keywords":[],"grade_filter":"THPT","year_terms":[],"search_strategy":"grade_based"}
- "lịch sử lớp 6" → {"keywords":[],"grade_filter":"6","year_terms":[],"search_strategy":"grade_based"}
- "Chiến thắng Bạch Đằng" → {"keywords":["Chiến thắng Bạch Đằng","Bạch Đằng","sông Bạch Đằng"],"grade_filter":null,"year_terms":["938","1288"],"search_strategy":"specific_event"}
"""


def _get_client():
    """Return Groq client if available, fallback to Gemini."""
    if settings.groq_api_key:
        from app.providers.groq_client import get_groq_client
        logger.info("[INTENT] Using Groq (%s)", settings.groq_model)
        return get_groq_client()
    if settings.google_api_key:
        from app.providers.gemini_client import get_gemini_client
        logger.warning("[INTENT] Groq key missing — falling back to Gemini")
        return get_gemini_client()
    return None


async def extract_search_intent(query: str) -> dict | None:
    """Use LLM to extract structured search parameters from user query."""
    logger.info("[INTENT] Extracting intent from query=%r", query)

    client = _get_client()
    if client is None:
        logger.warning("[INTENT] No LLM client available — skipping intent extraction")
        return None

    messages = [
        {"role": "system", "content": INTENT_SYSTEM},
        {"role": "user", "content": query},
    ]

    try:
        intent = await client.chat_json(messages=messages)
        if intent:
            logger.info("[INTENT] Extracted: %s", json.dumps(intent, ensure_ascii=False))
        return intent
    except Exception as e:
        logger.error("[INTENT] LLM extraction failed: %s", e)
        return None
