from typing import Any


LABELS = {
    "timeline": "Dòng thời gian",
    "characters": "Nhân vật",
    "climaxScene": "Cao trào",
    "aftermath": "Hệ quả",
    "quiz": "Câu hỏi ôn tập",
    "image": "Hình minh họa",
}


def check_story_event_coverage(parsed: dict[str, Any], template_key: str) -> dict[str, Any]:
    missing = []
    if not parsed.get("timeline"):
        missing.append(_issue("timeline", "Nội dung chưa có mốc thời gian rõ ràng."))
    if not parsed.get("characters"):
        missing.append(_issue("characters", "Chưa xác định được nhân vật chính."))
    if not parsed.get("climax"):
        missing.append(_issue("climaxScene", "Chưa có chi tiết cao trào đủ rõ để dựng cảnh tương tác."))
    if not parsed.get("aftermath"):
        missing.append(_issue("aftermath", "Chưa có hệ quả hoặc bài học sau sự kiện."))
    if len(parsed.get("sentences") or []) < 3:
        missing.append(_issue("quiz", "Chưa đủ dữ kiện để tạo câu hỏi ôn tập đáng tin cậy."))
    if not parsed.get("image_details"):
        missing.append(_issue("image", "Chưa có mô tả hình ảnh đủ cụ thể để tạo ảnh an toàn."))

    return {
        "missing": missing,
        "omittedSections": [],
        "userAcceptedMissing": False,
        "template": template_key or "universal",
    }


def accepted_coverage_report(report: dict[str, Any]) -> dict[str, Any]:
    missing = report.get("missing") or []
    return {
        "missing": missing,
        "omittedSections": [item["key"] for item in missing if item.get("key")],
        "userAcceptedMissing": True,
    }


def _issue(key: str, reason: str) -> dict[str, str]:
    return {"key": key, "label": LABELS[key], "reason": reason}
