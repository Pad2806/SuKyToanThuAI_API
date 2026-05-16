from app.generation.story_event_generator import parse_creator_content, payload_from_creator
from app.safety.coverage_gate import accepted_coverage_report, check_story_event_coverage
from app.workspace.story_event_payload import story_event_shell


def test_story_event_shell_has_required_shape():
    payload = story_event_shell("Trận mẫu", "battle", "custom_content", "creator")

    assert payload["pageType"] == "story-event"
    assert payload["flowType"] == "custom_content"
    assert payload["sourceMode"] == "creator"
    assert payload["eventData"]["featured"] is False
    assert payload["eventData"]["story"]["beats"] == []
    assert payload["coverageReport"]["userAcceptedMissing"] is False


def test_creator_payload_omits_user_accepted_missing_sections():
    parsed = parse_creator_content(
        "Tiêu đề: Sự kiện mẫu\n"
        "Năm 1288, một trận đánh diễn ra trên sông.\n"
        "Cao trào: Đội quân rơi vào thế bất lợi.\n"
        "Hệ quả: Chiến thắng được ghi nhớ.",
        "battle",
    )
    report = accepted_coverage_report(check_story_event_coverage(parsed, "battle"))

    payload = payload_from_creator(parsed, "battle", report)

    assert payload["pageType"] == "story-event"
    assert payload["coverageReport"]["userAcceptedMissing"] is True
    assert set(payload["coverageReport"]["omittedSections"])
    for section in payload["coverageReport"]["omittedSections"]:
        if section == "characters":
            assert payload["eventData"]["characters"] == []
        if section == "quiz":
            assert payload["eventData"]["quiz"] == []
