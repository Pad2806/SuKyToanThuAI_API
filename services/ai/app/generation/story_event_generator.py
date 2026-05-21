import re
from typing import Any

from app.generation.image_prompt_builder import build_image_assets
from app.generation.research_llm_transform import llm_transform_research
from app.generation.story_event_normalizer import normalize_story_event_payload
from app.rag.retriever import ChunkResult
from app.workspace.story_event_payload import story_event_shell


def parse_creator_content(content: str, template_key: str) -> dict[str, Any]:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    text = "\n".join(lines) or content.strip()
    sentences = _sentences(text)
    title = _field(lines, "tiêu đề") or _field(lines, "sự kiện") or (sentences[0][:80] if sentences else "Trang lịch sử mới")
    actors = _split(_field(lines, "nhân vật"))
    timeline = _timeline(sentences)
    result = _field(lines, "kết quả")
    return {
        "title": title,
        "summary": text[:420],
        "sentences": sentences,
        "year": _year(text),
        "location": _field(lines, "địa điểm"),
        "characters": [{"id": _slug(name), "name": name, "role": "Nhân vật", "side": "other", "portrait": None, "bio": name, "quote": None} for name in actors],
        "actors": actors,
        "timeline": timeline,
        "climax": _field(lines, "cao trào") or (sentences[1] if len(sentences) > 1 else None),
        "aftermath": _field(lines, "hệ quả") or result,
        "result": result,
        "image_details": _field(lines, "hình ảnh") or _field(lines, "bối cảnh"),
        "template": template_key or "universal",
    }


def payload_from_creator(parsed: dict[str, Any], template_key: str, coverage: dict[str, Any]) -> dict[str, Any]:
    payload = _payload_from_parsed(parsed, template_key, "custom_content", "creator", coverage)
    payload["moderation"] = {"status": "approved", "reason": None}
    return payload


def _clean_query(query: str) -> str:
    """Strip command-like prefixes from user queries to produce a clean title."""
    q = query.strip()
    # Remove common command prefixes (case-insensitive Vietnamese)
    prefixes = [
        r"^tạo\s+trang\s+(về\s+)?",
        r"^tạo\s+(về\s+)?",
        r"^viết\s+(về\s+)?",
        r"^tóm\s+tắt\s+(về\s+)?",
        r"^cho\s+tôi\s+(biết\s+)?(về\s+)?",
        r"^tìm\s+hiểu\s+(về\s+)?",
        r"^nghiên\s+cứu\s+(về\s+)?",
        r"^phân\s+tích\s+(về\s+)?",
        r"^hãy\s+",
        r"^giới\s+thiệu\s+(về\s+)?",
    ]
    for pattern in prefixes:
        q = re.sub(pattern, "", q, flags=re.IGNORECASE).strip()
    # Capitalize first letter
    return q[0].upper() + q[1:] if q else query


def payload_from_research_regex(query: str, chunks: list[ChunkResult], template_key: str) -> dict[str, Any]:
    clean_title = _clean_query(query)
    content = "\n".join(chunk.content[:900] for chunk in chunks)
    parsed = parse_creator_content(f"{clean_title}\n{content}", template_key)
    coverage = {"missing": [], "omittedSections": [], "userAcceptedMissing": False}
    payload = _payload_from_parsed(parsed, template_key, "system_data", "research", coverage)
    payload["citations"] = [_citation(chunk) for chunk in chunks]
    return payload


async def payload_from_research(query: str, chunks: list[ChunkResult], template_key: str) -> dict[str, Any]:
    # Clean user query for professional title
    clean_q = _clean_query(query)
    # Try LLM first
    llm_result = await llm_transform_research(clean_q, chunks, template_key)
    if llm_result:
        # Sanitize LLM output
        llm_result = _sanitize_parsed(llm_result)

        # Create a shell payload
        payload = story_event_shell(llm_result["title"], template_key, "system_data", "research", llm_result.get("summary") or "")
        
        # Merge LLM result into eventData
        payload["eventData"].update(llm_result)
        
        # Keep coverage and citations
        payload["coverageReport"] = {"missing": [], "omittedSections": [], "userAcceptedMissing": False}
        payload["citations"] = [_citation(chunk) for chunk in chunks]
        
        return normalize_story_event_payload(payload, llm_result["title"], template_key, "system_data", "research")
        
    # Fallback to regex parser
    return payload_from_research_regex(query, chunks, template_key)


def _payload_from_parsed(parsed: dict[str, Any], template_key: str, flow_type: str, source_mode: str, coverage: dict[str, Any]) -> dict[str, Any]:
    payload = story_event_shell(parsed["title"], template_key, flow_type, source_mode, parsed["summary"])
    event = payload["eventData"]
    omitted = set(coverage.get("omittedSections") or [])
    event.update({
        "year": parsed.get("year"),
        "location": parsed.get("location"),
        "actors": parsed.get("actors") or [],
        "result": parsed.get("result"),
        "characters": [] if "characters" in omitted else parsed.get("characters", []),
        "timeline": [] if "timeline" in omitted else parsed.get("timeline", []),
        "climaxScene": None if "climaxScene" in omitted else _climax_scene(parsed),
        "aftermath": None if "aftermath" in omitted else _aftermath(parsed),
        "takeaway": None if "aftermath" in omitted else _takeaway(parsed),
        "quiz": [] if "quiz" in omitted else _quiz(parsed),
        "story": {"templateType": template_key or "universal", "beats": _beats(parsed, omitted)},
    })
    payload["coverageReport"] = coverage
    payload["assets"] = build_image_assets(parsed, coverage)
    return normalize_story_event_payload(payload, parsed["title"], template_key, flow_type, source_mode)


def _beats(parsed: dict[str, Any], omitted: set[str]) -> list[dict[str, Any]]:
    beats = [{"type": "setup", "title": parsed["title"], "blocks": [{"type": "text", "body": parsed["summary"]}]}]
    if "timeline" not in omitted and parsed.get("timeline"):
        beats.append({"type": "rising", "title": "Diễn biến", "blocks": []})
    if "climaxScene" not in omitted and parsed.get("climax"):
        beats.append({"type": "climax", "title": "Cao trào", "blocks": [{"type": "text", "body": parsed["climax"]}]})
    if "aftermath" not in omitted and parsed.get("aftermath"):
        beats.append({"type": "falling", "title": "Hệ quả", "blocks": [{"type": "text", "body": parsed["aftermath"]}]})
    beats.append({"type": "takeaway", "title": "Ghi nhớ", "blocks": [{"type": "text", "body": parsed["summary"][:260]}]})
    return beats


def _climax_scene(parsed: dict[str, Any]) -> dict[str, Any] | None:
    """Build climaxScene from AI-generated data with multi-phase support."""
    scene = parsed.get("climaxScene")
    if scene and isinstance(scene, dict) and scene.get("phases"):
        # AI returned a full climaxScene object — use it directly
        return {
            "title": scene.get("title") or "Khoảnh khắc trọng tâm",
            "backgroundImage": scene.get("backgroundImage"),
            "phases": scene["phases"][:3],  # Max 3 phases
            "hotspots": scene.get("hotspots") or [],
        }
    # Fallback: wrap single climax text into one phase
    climax_text = parsed.get("climax")
    if not climax_text:
        return None
    return {
        "title": "Khoảnh khắc trọng tâm",
        "backgroundImage": None,
        "phases": [{"id": "phase-1", "label": "Trọng tâm", "summary": climax_text[:120], "description": climax_text}],
        "hotspots": [],
    }


def _aftermath(parsed: dict[str, Any]) -> dict[str, Any] | None:
    if not parsed.get("aftermath"):
        return None
    return {"title": "Sau sự kiện", "stats": [], "before": {"title": "Trước đó", "items": []}, "after": {"title": "Sau đó", "items": [parsed["aftermath"]]}}


def _takeaway(parsed: dict[str, Any]) -> dict[str, str] | None:
    return {"happened": parsed["summary"][:180], "whyItMatters": parsed.get("aftermath") or parsed["summary"][:180], "lesson": "Nội dung được dựng từ nguồn đã cung cấp."}


def _quiz(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    if len(parsed.get("sentences") or []) < 3:
        return []
    return [{"id": "q1", "question": f"Nội dung chính của {parsed['title']} là gì?", "options": [parsed["summary"][:80], "Một sự kiện không liên quan", "Một truyền thuyết khác"], "correct": 0, "explanation": "Đáp án dựa trên nội dung người dùng hoặc nguồn hệ thống cung cấp."}]


def _timeline(sentences: list[str]) -> list[dict[str, str]]:
    return [{"id": f"m{i}", "year": str(_year(s) or ""), "month": "", "title": s[:60], "description": s} for i, s in enumerate(sentences, 1) if _year(s)]


def _citation(chunk: ChunkResult) -> dict[str, Any]:
    return {"sourceType": "official_text", "sourceId": str(chunk.id), "title": chunk.title, "sourceRefType": "event", "sourceRefId": (chunk.event_slugs or [None])[0], "chunkId": str(chunk.id), "metadata": {"score": chunk.score, "eventSlugs": chunk.event_slugs}}


def _field(lines: list[str], key: str) -> str | None:
    prefix = key.lower()
    for line in lines:
        if line.lower().startswith(prefix):
            return line.split(":", 1)[-1].strip()
    return None


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?。])\s+|\n+", text) if len(part.strip()) > 20]


def _year(text: str) -> int | None:
    match = re.search(r"(?<!\d)(-?\d{3,4})(?!\d)", text)
    return int(match.group(1)) if match else None


def _split(value: str | None) -> list[str]:
    return [item.strip() for item in re.split(r"[,;]", value or "") if item.strip()]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "character"


# ── Text sanitization ────────────────────────────────────────────

_LABEL_PREFIXES = re.compile(
    r'^["\']?\s*(?:Tiêu đề|Khoảnh Khắc|Sự kiện|Tóm tắt|Mô tả|Bối cảnh)\s*[:：]\s*',
    re.IGNORECASE | re.MULTILINE,
)


def _strip_label(text: str | None) -> str | None:
    """Remove label prefixes like 'Tiêu đề:' from text."""
    if not text:
        return text
    return _LABEL_PREFIXES.sub('', text).strip()


def _sanitize_parsed(parsed: dict[str, Any]) -> dict[str, Any]:
    """Strip label prefixes from all user-facing text fields."""
    for key in ('title', 'summary', 'excerpt', 'climax', 'aftermath', 'result'):
        if isinstance(parsed.get(key), str):
            parsed[key] = _strip_label(parsed[key])

    # Clean actors — should be short names, not sentences
    if isinstance(parsed.get('actors'), list):
        parsed['actors'] = [a for a in parsed['actors'] if len(a) < 40]

    # Clean characters
    for char in parsed.get('characters', []):
        if isinstance(char, dict):
            for field in ('name', 'bio', 'role'):
                if isinstance(char.get(field), str):
                    char[field] = _strip_label(char[field])

    # Clean takeaway
    tw = parsed.get('takeaway')
    if isinstance(tw, dict):
        for field in ('happened', 'whyItMatters', 'lesson'):
            if isinstance(tw.get(field), str):
                tw[field] = _strip_label(tw[field])

    return parsed
