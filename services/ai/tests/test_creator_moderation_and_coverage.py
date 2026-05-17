from app.generation.story_event_generator import parse_creator_content
from app.safety.content_moderation import moderate_image_prompt, moderate_text
from app.safety.coverage_gate import check_story_event_coverage


def test_creator_text_moderation_rejects_unsafe_content():
    result = moderate_text("Nội dung này yêu cầu porn trong bối cảnh lịch sử.")

    assert result.status == "rejected"
    assert "sexual" in result.categories


def test_image_prompt_moderation_rejects_unsafe_prompt():
    result = moderate_image_prompt("Tạo ảnh nude nhân vật lịch sử trong cảnh minh họa.")

    assert result.status == "rejected"


def test_coverage_reports_missing_sections_without_inventing_data():
    parsed = parse_creator_content("Tiêu đề: Một sự kiện ngắn\nChỉ có một mô tả chung chung về quá khứ.", "universal")
    report = check_story_event_coverage(parsed, "universal")
    missing_keys = {item["key"] for item in report["missing"]}

    assert "timeline" in missing_keys
    assert "characters" in missing_keys
    assert report["userAcceptedMissing"] is False
