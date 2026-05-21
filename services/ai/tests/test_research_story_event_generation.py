from app.generation.story_event_generator import payload_from_research
from app.rag.retriever import ChunkResult


def test_research_payload_uses_citations_and_story_event_shape():
    chunk = ChunkResult(
        id="unit-1",
        title="Nguồn mẫu",
        content="Năm 1288, sự kiện diễn ra với nhiều chi tiết lịch sử quan trọng.",
        event_slugs=["chien-thang-bach-dang-1288"],
        score=0.9,
    )

    payload = payload_from_research("Bạch Đằng 1288", [chunk], "battle")

    assert payload["pageType"] == "story-event"
    assert payload["flowType"] == "system_data"
    assert payload["sourceMode"] == "research"
    assert payload["citations"][0]["sourceId"] == "unit-1"
    assert payload["eventData"]["story"]["templateType"] == "battle"
