import pytest

from app.generation import story_event_generator
from app.generation.grade_curriculum_llm_prompt import build_grade_curriculum_llm_messages
from app.generation.orchestrator import _missing_intent_keywords, _missing_required_query_terms
from app.generation.story_event_generator import payload_from_research
from app.rag.retriever import ChunkResult, _expand_grade_filters


@pytest.mark.anyio
async def test_research_payload_uses_citations_and_story_event_shape(monkeypatch):
    async def no_llm_transform(*_args, **_kwargs):
        return None

    monkeypatch.setattr(story_event_generator, "llm_transform_research", no_llm_transform)

    chunk = ChunkResult(
        id="unit-1",
        title="Nguồn mẫu",
        content="Năm 1288, sự kiện diễn ra với nhiều chi tiết lịch sử quan trọng.",
        event_slugs=["chien-thang-bach-dang-1288"],
        score=0.9,
    )

    payload = await payload_from_research("Bạch Đằng 1288", [chunk], "battle")

    assert payload["pageType"] == "story-event"
    assert payload["flowType"] == "system_data"
    assert payload["sourceMode"] == "research"
    assert payload["citations"][0]["sourceId"] == "unit-1"
    assert payload["eventData"]["story"]["templateType"] == "battle"


def test_required_query_terms_reject_unmatched_specific_subject():
    chunks = [
        ChunkResult(
            id="otu-yasuo-battle-of-silver-wind",
            title="Trận chiến Thung lũng Gió Bạc",
            content="Nhân vật trung tâm của sự kiện là Yasuo tại Ionia.",
            event_slugs=["battle-of-silver-wind", "yasuo-rise"],
            score=16,
        )
    ]

    assert _missing_required_query_terms("trận chiến naruto", chunks) == ["naruto"]
    assert _missing_required_query_terms("trận chiến yasuo", chunks) == []


def test_required_query_terms_allow_known_unaccented_or_accented_subjects():
    chunks = [
        ChunkResult(
            id="otu-chien-thang-dien-bien-phu-1954",
            title="Chiến thắng Điện Biên Phủ năm 1954",
            content="Chiến dịch Điện Biên Phủ kết thúc năm 1954.",
            event_slugs=["chien-thang-dien-bien-phu-1954"],
            score=9,
        )
    ]

    assert _missing_required_query_terms("tóm tắt cuộc chiến điện biên phủ", chunks) == []
    assert _missing_required_query_terms("tom tat cuoc chien dien bien phu", chunks) == []


def test_grade_filter_expands_class_tags_to_level_tags():
    assert _expand_grade_filters("8") == ["8", "lớp 8"]
    assert _expand_grade_filters("lớp 8") == ["lớp 8", "8"]
    assert _expand_grade_filters("12") == ["12", "lớp 12"]
    assert _expand_grade_filters("lớp 12") == ["lớp 12", "12"]
    assert _expand_grade_filters("THPT") == ["THPT", "lớp 10", "lớp 11", "lớp 12"]


def test_intent_keyword_coverage_allows_non_contiguous_topic_terms():
    chunks = [
        ChunkResult(
            id="otu-dien-bien-phu",
            title="Chiến thắng Điện Biên Phủ năm 1954",
            content="Chiến thắng kết thúc 9 năm kháng chiến chống thực dân Pháp.",
            event_slugs=["chien-thang-dien-bien-phu-1954"],
            score=1.5,
        )
    ]

    assert _missing_intent_keywords(["kháng chiến chống Pháp"], chunks) == []


def test_grade_curriculum_prompt_exposes_chapter_lesson_codes():
    chunk = ChunkResult(
        id="SU8-CH4-B10",
        title="Bài 10: Công xã Pa-ri (năm 1871)",
        content="Nội dung bài học.",
        event_slugs=[],
        score=1,
    )

    messages = build_grade_curriculum_llm_messages("tóm tắt lịch sử lớp 8", [chunk], "8")
    user_prompt = messages[1]["content"]

    assert "Mã tài liệu: SU8-CH4-B10" in user_prompt
    assert "cùng CHx thì chung một era" in user_prompt
