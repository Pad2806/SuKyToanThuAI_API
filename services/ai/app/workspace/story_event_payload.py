from copy import deepcopy
from typing import Any

DEFAULT_IMAGE = "/images/generated/parchment.png"
DEFAULT_THEME = "vietnamese-history"


def story_event_shell(
    title: str,
    template_key: str,
    flow_type: str,
    source_mode: str,
    summary: str = "",
) -> dict[str, Any]:
    clean_title = (title or "Trang lịch sử mới").strip()
    clean_summary = (summary or clean_title).strip()
    return {
        "pageType": "story-event",
        "flowType": flow_type,
        "sourceMode": source_mode,
        "title": clean_title,
        "eventData": {
            "id": "",
            "slug": "",
            "title": clean_title,
            "eraId": None,
            "eraSlug": None,
            "year": None,
            "gradeTags": [],
            "topics": [],
            "type": template_key or "universal",
            "featured": False,
            "summary": clean_summary,
            "excerpt": clean_summary[:220],
            "image": None,
            "fallbackImage": DEFAULT_IMAGE,
            "location": None,
            "actors": [],
            "opponent": None,
            "result": None,
            "characters": [],
            "timeline": [],
            "climaxScene": None,
            "aftermath": None,
            "takeaway": None,
            "quiz": [],
            "story": {"templateType": template_key or "universal", "beats": []},
            "theme": DEFAULT_THEME,
            "relatedEventSlugs": [],
        },
        "citations": [],
        "assets": [],
        "coverageReport": {
            "missing": [],
            "omittedSections": [],
            "userAcceptedMissing": False,
        },
        "moderation": {"status": "approved", "reason": None},
    }


def assign_page_identity(payload: dict[str, Any], page_id: Any) -> dict[str, Any]:
    result = deepcopy(payload)
    page_id_text = str(page_id)
    event_data = result.setdefault("eventData", {})
    event_data["id"] = page_id_text
    event_data["slug"] = f"ai-page-{page_id_text}"
    return result
