from dataclasses import dataclass


@dataclass(frozen=True)
class ModerationResult:
    status: str
    reason: str | None = None
    categories: list[str] | None = None

    def to_payload(self) -> dict:
        return {
            "status": self.status,
            "reason": self.reason,
            "categories": self.categories or [],
        }


BLOCKED_TERMS = {
    "sexual": ["khiêu dâm", "porn", "sex", "nude", "khỏa thân"],
    "hate": ["diệt chủng", "thù hằn chủng tộc", "phân biệt chủng tộc"],
    "self_harm": ["tự sát", "tự tử", "cắt cổ tay"],
    "graphic_violence": ["máu me chi tiết", "tra tấn chi tiết", "chặt đầu chi tiết"],
}


def moderate_text(content: str) -> ModerationResult:
    text = (content or "").lower()
    if len(text.strip()) < 20:
        return ModerationResult("rejected", "Nội dung quá ngắn để kiểm duyệt và dựng trang.", ["too_short"])

    hits = [
        category
        for category, terms in BLOCKED_TERMS.items()
        if any(term in text for term in terms)
    ]
    if hits:
        return ModerationResult(
            "rejected",
            "Nội dung có dấu hiệu vi phạm tiêu chuẩn an toàn, nên không thể tạo trang hoặc ảnh.",
            hits,
        )
    return ModerationResult("approved")


def moderate_image_prompt(prompt: str) -> ModerationResult:
    result = moderate_text(prompt or "prompt an toàn đủ dài")
    if result.status == "rejected":
        return ModerationResult("rejected", "Prompt ảnh không đạt tiêu chuẩn an toàn.", result.categories)
    return ModerationResult("approved")
