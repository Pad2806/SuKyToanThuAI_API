from typing import Any

from app.safety.content_moderation import moderate_image_prompt


def build_image_assets(parsed: dict[str, Any], coverage_report: dict[str, Any]) -> list[dict[str, Any]]:
    omitted = set(coverage_report.get("omittedSections") or [])
    if "image" in omitted:
        return []

    title = parsed.get("title") or "Trang lịch sử"
    details = parsed.get("image_details") or parsed.get("summary") or title
    prompt = f"Minh họa lịch sử Việt Nam, {title}. Bối cảnh: {details}. Phong cách cinematic, giáo dục, không bạo lực đồ họa."
    moderation = moderate_image_prompt(prompt)
    status = "queued" if moderation.status == "approved" else "failed"
    return [{
        "slot": "hero",
        "assetType": "image",
        "prompt": prompt,
        "publicUrl": None,
        "status": status,
        "metadata": {"moderation": moderation.to_payload()},
    }]
