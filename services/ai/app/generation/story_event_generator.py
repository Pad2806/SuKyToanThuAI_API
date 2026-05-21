import re
from typing import Any

from app.chains.analyze_content_chain import analyze_contents
from app.generation.image_prompt_builder import build_image_assets
from app.generation.story_event_normalizer import normalize_story_event_payload
from app.rag.retriever import ChunkResult
from app.workspace.story_event_payload import story_event_shell


# def parse_creator_content(content: str, template_key: str) -> dict[str, Any]:
#     lines = [line.strip() for line in content.splitlines() if line.strip()]
#     text = "\n".join(lines) or content.strip()
#     sentences = _sentences(text)
#     title = _field(lines, "tiêu đề") or _field(lines, "sự kiện") or (sentences[0][:80] if sentences else "Trang lịch sử mới")
#     actors = _split(_field(lines, "nhân vật"))
#     timeline = _timeline(sentences)
#     result = _field(lines, "kết quả")
#     return {
#         "title": title,
#         "summary": text[:420],
#         "sentences": sentences,
#         "year": _year(text),
#         "location": _field(lines, "địa điểm"),
#         "characters": [{"id": _slug(name), "name": name, "role": "Nhân vật", "side": "other", "portrait": None, "bio": name, "quote": None} for name in actors],
#         "actors": actors,
#         "timeline": timeline,
#         "climax": _field(lines, "cao trào") or (sentences[1] if len(sentences) > 1 else None),
#         "aftermath": _field(lines, "hệ quả") or result,
#         "result": result,
#         "image_details": _field(lines, "hình ảnh") or _field(lines, "bối cảnh"),
#         "template": template_key or "universal",
#     }

def parse_creator_content(content: str) -> dict[str, Any]:
    parsed = analyze_contents(content)
    print(f"Sau khi parsed: template={parsed.get('template')}", parsed)
    return parsed
    


def payload_from_creator(parsed: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    template_key = parsed.get("template") or "universal"
    payload = _payload_from_parsed(parsed, template_key, "custom_content", "creator", coverage)
    payload["moderation"] = {"status": "approved", "reason": None}
    return payload


def payload_from_research(query: str, chunks: list[ChunkResult]) -> dict[str, Any]:
    content = "\n".join(chunk.content[:900] for chunk in chunks)
    parsed = parse_creator_content(f"Tiêu đề: {query}\n{content}")
    template_key = parsed.get("template") or "universal"
    coverage = {"missing": [], "omittedSections": [], "userAcceptedMissing": False}
    payload = _payload_from_parsed(parsed, template_key, "system_data", "research", coverage)
    payload["citations"] = [_citation(chunk) for chunk in chunks]
    return payload


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
        beats.append({"type": "rising", "title": "Diễn biến", "blocks": [{"type": "text", "body": "Các mốc chính được trích từ nội dung đầu vào."}]})
    if "climaxScene" not in omitted and parsed.get("climax"):
        climax_val = parsed.get("climax")
        if isinstance(climax_val, str):
            climax_body = climax_val
        else:
            climax_body = "\n\n".join(p.get("description", "") for p in climax_val.get("phases", [])) or climax_val.get("title", "")
        beats.append({"type": "climax", "title": "Cao trào", "blocks": [{"type": "text", "body": climax_body}]})
    if "aftermath" not in omitted and parsed.get("aftermath"):
        beats.append({"type": "falling", "title": "Hệ quả", "blocks": [{"type": "text", "body": parsed["aftermath"]}]})
    beats.append({"type": "takeaway", "title": "Ghi nhớ", "blocks": [{"type": "text", "body": parsed["summary"][:260]}]})
    return beats


def _climax_scene(parsed: dict[str, Any]) -> dict[str, Any] | None:
    climax = parsed.get("climax")
    if not climax:
        return None
        
    if isinstance(climax, str):
        return {
            "title": "Khoảnh khắc trọng tâm",
            "backgroundImage": "/images/generated/parchment.png",
            "phases": [{
                "id": "phase-1",
                "label": "Trọng tâm",
                "summary": climax[:120],
                "description": climax,
                "keyDetail": None
            }],
            "hotspots": []
        }
        
    # Nếu climax là dictionary cấu trúc phức hợp
    phases = []
    for i, p in enumerate(climax.get("phases", [])):
        phases.append({
            "id": p.get("id") or f"p{i+1}",
            "label": p.get("label", f"Giai đoạn {i+1}"),
            "summary": p.get("summary", ""),
            "description": p.get("description", ""),
            "keyDetail": p.get("key_detail") or p.get("keyDetail") or None
        })
        
    hotspots = []
    for i, hs in enumerate(climax.get("hotspots", [])):
        hotspots.append({
            "id": hs.get("id") or f"hs{i+1}",
            "x": hs.get("x", 50),
            "y": hs.get("y", 50),
            "label": hs.get("label", ""),
            "description": hs.get("description", "")
        })
        
    return {
        "title": climax.get("title", "Khoảnh khắc trọng tâm"),
        "backgroundImage": "/images/generated/parchment.png",
        "phases": phases,
        "hotspots": hotspots
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
