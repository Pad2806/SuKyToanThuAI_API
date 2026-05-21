import logging
import re
import unicodedata
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ── Regex-based time_period detection (fallback for Groq) ────────
_TIME_PERIOD_PATTERNS = [
    # "từ thế kỷ X đến/tới Y", "thế kỉ 16 tới 20", "thế kỉ 18 đến nay"
    re.compile(r"thế\s*k[ỷỉ]\s*\d+\s*(đến|tới|[-–])\s*(thế\s*k[ỷỉ]\s*)?(\d+|nay)", re.IGNORECASE),
    # "từ năm XXXX đến XXXX", "giai đoạn 1945-1975", "từ năm 1858 đến nay"
    re.compile(r"(từ\s+năm|giai\s+đoạn)\s*\d{3,4}\s*(đến|tới|[-–])\s*(\d{3,4}|nay)", re.IGNORECASE),
    # Named eras: "lịch sử hiện đại", "thời phong kiến", "giai đoạn kháng chiến"
    re.compile(
        r"(lịch\s*sử|thời(\s*kỳ)?|giai\s*đoạn)\s+"
        r"(hiện\s*đại|cận\s*đại|cổ\s*đại|trung\s*đại|phong\s*kiến|cận\s*hiện\s*đại|"
        r"bắc\s*thuộc|pháp\s*thuộc|đổi\s*mới|kháng\s*chiến)",
        re.IGNORECASE,
    ),
    # "tóm tắt lịch sử từ ... đến ..."
    re.compile(r"tóm\s*tắt\s+lịch\s*sử\s+từ\s+.+\s+(đến|tới)", re.IGNORECASE),
    # Single century: "thế kỷ 10", "lịch sử thế kỉ 19"
    re.compile(r"thế\s*k[ỷỉ]\s*\d{1,2}\b", re.IGNORECASE),
]


def _is_time_period_query(query: str) -> bool:
    """Regex fallback: detect time-period queries that Groq might misclassify."""
    for pattern in _TIME_PERIOD_PATTERNS:
        if pattern.search(query):
            return True
    return False


# Mapping: century number → representative years for DB search
_CENTURY_YEAR_MAP: dict[int, list[str]] = {
    1:  ["40", "43", "179 TCN"],
    2:  ["179 TCN", "40", "248"],
    3:  ["248"],
    10: ["938", "939", "968"],
    11: ["1009", "1010"],
    12: ["1225"],
    13: ["1225", "1258", "1288"],
    14: ["1400"],
    15: ["1428", "1471"],
    16: ["1527", "1558"],
    17: ["1627", "1672"],
    18: ["1771", "1789", "1802"],
    19: ["1802", "1858", "1884", "1885"],
    20: ["1930", "1945", "1954", "1975"],
    21: ["1986", "2000"],
}

# Current century for "đến nay" queries
_CURRENT_CENTURY = 21


def _century_range_intent_from_query(query: str) -> dict | None:
    """Extract century (single or range) from queries.

    Handles:
      - Range: 'thế kỉ 18 đến nay', 'thế kỷ 16 tới 20'
      - Single: 'thế kỷ 10', 'lịch sử thế kỉ 19'
    """
    # Try range pattern first: "thế kỷ X đến/tới Y|nay"
    m = re.search(
        r"thế\s*k[ỷỉ]\s*(\d+)\s*(?:đến|tới|[-–])\s*(?:thế\s*k[ỷỉ]\s*)?(\d+|nay)",
        query,
        re.IGNORECASE,
    )
    if m:
        start_century = int(m.group(1))
        end_raw = m.group(2).strip().lower()
        end_century = _CURRENT_CENTURY if end_raw == "nay" else int(end_raw)
    else:
        # Fallback: single century "thế kỷ 10"
        m2 = re.search(r"thế\s*k[ỷỉ]\s*(\d{1,2})\b", query, re.IGNORECASE)
        if not m2:
            return None
        start_century = int(m2.group(1))
        end_century = start_century

    if start_century > end_century or start_century < 1:
        return None

    # Collect all representative years for the range
    year_terms: list[str] = []
    for c in range(start_century, end_century + 1):
        year_terms.extend(_CENTURY_YEAR_MAP.get(c, []))

    # De-duplicate while preserving order
    seen: set[str] = set()
    unique_years: list[str] = []
    for y in year_terms:
        if y not in seen:
            seen.add(y)
            unique_years.append(y)

    if not unique_years:
        return None

    return {
        "keywords": [],
        "grade_filter": None,
        "year_terms": unique_years,
        "search_strategy": "time_period",
    }


def _time_period_intent_from_query(query: str) -> dict | None:
    """Build deterministic intent for named historical periods or century ranges."""
    normalized = _normalize_search_text(query)
    period_map = [
        ("can hien dai", ["1858", "1945", "1954", "1975", "2000"]),
        ("can dai", ["1858", "1884", "1930", "1945"]),
        ("hien dai", ["1945", "1954", "1975", "2000"]),
        ("co dai", ["2879 TCN", "179 TCN"]),
        ("bac thuoc", ["179 TCN", "938"]),
        ("phong kien", ["939", "1009", "1225", "1400", "1428", "1802"]),
        ("trung dai", ["939", "1009", "1225", "1400", "1428", "1802"]),
        ("phap thuoc", ["1858", "1884", "1930", "1945"]),
        ("doi moi", ["1986", "2000"]),
        ("khang chien", ["1945", "1954", "1975"]),
    ]
    for marker, year_terms in period_map:
        if marker in normalized:
            return {
                "keywords": [],
                "grade_filter": None,
                "year_terms": year_terms,
                "search_strategy": "time_period",
            }

    # Fallback: try to extract century range (e.g. "thế kỉ 18 đến nay")
    return _century_range_intent_from_query(query)

# ── Regex-based grade_based detection ────────
_GRADE_PATTERNS = [
    # "lịch sử lớp 12", "lớp 6", "lớp 10"
    re.compile(r"lớp\s*\d{1,2}", re.IGNORECASE),
    # "THPT", "THCS", "TH" viết tắt
    re.compile(r"\b(THPT|THCS|TH)\b", re.IGNORECASE),
    # Viết đầy đủ
    re.compile(
        r"(trung\s*học\s*phổ\s*thông|trung\s*học\s*cơ\s*sở|tiểu\s*học"
        r"|phổ\s*thông|cơ\s*sở|cấp\s*[123])",
        re.IGNORECASE,
    ),
]

def _is_grade_query(query: str) -> bool:
    """Regex fallback: detect grade-based queries."""
    for pattern in _GRADE_PATTERNS:
        if pattern.search(query):
            return True
    return False


def _extract_grade_filter(query: str) -> str | None:
    """Extract specific grade number or level code from query."""
    import re as _re
    # Try specific class number first: "lớp 12" → "12"
    m = _re.search(r"lớp\s*(\d{1,2})", query, _re.IGNORECASE)
    if m:
        return m.group(1)
    # Try level codes
    if _re.search(r"\bTHPT\b", query, _re.IGNORECASE) or _re.search(r"trung\s*học\s*phổ\s*thông|phổ\s*thông|cấp\s*3", query, _re.IGNORECASE):
        return "THPT"
    if _re.search(r"\bTHCS\b", query, _re.IGNORECASE) or _re.search(r"trung\s*học\s*cơ\s*sở|cơ\s*sở|cấp\s*2", query, _re.IGNORECASE):
        return "THCS"
    if _re.search(r"\bTH\b", query, _re.IGNORECASE) or _re.search(r"tiểu\s*học|cấp\s*1", query, _re.IGNORECASE):
        return "TH"
    return None


_QUERY_STOPWORDS = {
    "ai",
    "anh",
    "bai",
    "biet",
    "cho",
    "chien",
    "co",
    "cuoc",
    "cua",
    "dang",
    "dien",
    "gioi",
    "hay",
    "ke",
    "lich",
    "mot",
    "noi",
    "su",
    "tat",
    "tao",
    "the",
    "thuat",
    "tom",
    "toi",
    "tran",
    "trang",
    "ve",
    "viet",
}


def _normalize_search_text(value: str) -> str:
    text_value = unicodedata.normalize("NFD", value.lower())
    without_marks = "".join(char for char in text_value if unicodedata.category(char) != "Mn")
    return without_marks.replace("đ", "d")


def _extract_required_query_terms(query: str) -> list[str]:
    normalized = _normalize_search_text(query)
    words = re.findall(r"[a-z0-9]+", normalized)
    return [
        word
        for word in words
        if len(word) >= 3 and word not in _QUERY_STOPWORDS
    ]


def _missing_required_query_terms(query: str, chunks: list) -> list[str]:
    required_terms = _extract_required_query_terms(query)
    if not required_terms:
        return []

    corpus = _normalize_search_text(
        " ".join(
            f"{chunk.title} {chunk.content} {' '.join(chunk.event_slugs or [])}"
            for chunk in chunks[:5]
        )
    )
    return [term for term in required_terms if term not in corpus]


def _missing_intent_keywords(intent_keywords: list[str], chunks: list) -> list[str]:
    if not intent_keywords:
        return []

    corpus = _normalize_search_text(
        " ".join(
            f"{chunk.title} {chunk.content} {' '.join(chunk.event_slugs or [])}"
            for chunk in chunks[:5]
        )
    )
    missing = []
    for keyword in intent_keywords:
        keyword_terms = _extract_required_query_terms(keyword)
        if keyword_terms:
            if not all(term in corpus for term in keyword_terms):
                missing.append(keyword)
        elif _normalize_search_text(keyword) not in corpus:
            missing.append(keyword)
    return missing


from app.generation.story_event_generator import (
    parse_creator_content,
    payload_from_creator,
    payload_from_research,
)
from app.generation.era_timeline_generator import payload_from_era_timeline
from app.generation.image_prompt_builder import generate_event_images
from app.safety.content_moderation import moderate_text
from app.safety.coverage_gate import accepted_coverage_report, check_story_event_coverage
from app.rag.retriever import retrieve
from app.rag.search_intent_extractor import extract_search_intent
from app.workspace.page_manager import PageManager
from app.workspace.story_event_payload import story_event_shell


class GenerationOrchestrator:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.page_manager = PageManager(db)

    async def research(self, query: str, template: str, user_id: UUID) -> dict:
        logger.info("[ORCH] research() called | query=%r | template=%r | user_id=%s", query, template, user_id)
        request_id = await self.page_manager.create_request(
            user_id=user_id,
            flow_type="system_data",
            intent="generate_page",
            template=template,
            query_text=query,
        )
        chunks = await retrieve(query, self.db)
        if not chunks:
            await self.page_manager.finish_request(request_id, "no_data", failure_reason="Không tìm thấy dữ liệu phù hợp.")
            await self.db.commit()
            return {
                "status": "no_data",
                "detail": "Không tìm thấy dữ liệu phù hợp trong kho sử liệu hiện có.",
            }

        payload = payload_from_research(query, chunks, template)
        return await self.page_manager.save_story_event_page(
        logger.info("[ORCH] request_id=%s", request_id)

        # Step 1: LLM extracts search intent from user query
        intent = await extract_search_intent(query)
        logger.info("[ORCH] Intent extracted: %s", intent)

        # Step 2: Detect template — THREE-LAYER detection
        # Layer 1: Regex time_period
        regex_time_hit = _is_time_period_query(query)
        # Layer 2: Regex grade_based
        regex_grade_hit = _is_grade_query(query)
        # Layer 3: Groq LLM classification
        groq_time_hit = intent and intent.get("search_strategy") == "time_period"
        groq_grade_hit = intent and intent.get("search_strategy") == "grade_based"

        # Failsafe: if regex detected grade but Groq missed it, patch intent
        if regex_grade_hit and intent:
            # Always ensure grade_filter is set
            if not intent.get("grade_filter"):
                intent["grade_filter"] = _extract_grade_filter(query)
                logger.info("[ORCH] Patched grade_filter → %s (regex extraction)", intent["grade_filter"])
            # Only override strategy to grade_based if LLM has NO specific keywords.
            # "cách mạng tháng 8 lớp 12" → keep specific_event + grade_filter
            # "lịch sử lớp 12"           → override to grade_based
            has_specific_keywords = bool(intent.get("keywords"))
            if intent.get("search_strategy") != "grade_based" and not has_specific_keywords:
                intent["search_strategy"] = "grade_based"
                logger.info("[ORCH] Patched intent strategy → grade_based (regex override, no keywords)")
            elif has_specific_keywords:
                logger.info("[ORCH] Keeping strategy=%s (has keywords=%s + grade_filter=%s)",
                            intent.get("search_strategy"), intent.get("keywords"), intent.get("grade_filter"))
        elif regex_grade_hit and not intent:
            intent = {"search_strategy": "grade_based", "grade_filter": _extract_grade_filter(query), "keywords": [], "year_terms": []}
            logger.info("[ORCH] Created intent from regex: %s", intent)

        regex_time_intent = _time_period_intent_from_query(query) if regex_time_hit else None
        if regex_time_intent and intent:
            if intent.get("search_strategy") != "time_period":
                intent.update(regex_time_intent)
                logger.info("[ORCH] Patched intent strategy → time_period (regex override): %s", intent)
            elif not intent.get("year_terms"):
                intent["year_terms"] = regex_time_intent["year_terms"]
                logger.info("[ORCH] Patched time_period year_terms → %s", intent["year_terms"])
        elif regex_time_intent and not intent:
            intent = regex_time_intent
            logger.info("[ORCH] Created time_period intent from regex: %s", intent)

        is_era_timeline = regex_time_hit or regex_grade_hit or groq_time_hit or groq_grade_hit
        if is_era_timeline:
            template = "era-timeline"
            logger.info(
                "[ORCH] Detected era_timeline compatible query (regex_time=%s, regex_grade=%s, groq_time=%s, groq_grade=%s)",
                regex_time_hit, regex_grade_hit, groq_time_hit, groq_grade_hit,
            )

        # Step 3: RAG retrieval (higher limit for era-timeline)
        retrieval_limit = 15 if is_era_timeline else 5
        chunks = await retrieve(query, self.db, limit=retrieval_limit, intent=intent)
        logger.info("[ORCH] retrieve() returned %d chunks (limit=%d)", len(chunks), retrieval_limit)

        if not chunks:
            logger.warning("[ORCH] No chunks found for query=%r — returning no_data", query)
            await self.page_manager.finish_request(request_id, "no_data", failure_reason="Không tìm thấy dữ liệu phù hợp.")
            await self.db.commit()
            return {
                "status": "no_data",
                "detail": "Sự kiện này chưa có trong kho sử liệu. Hãy thử tìm kiếm các sự kiện khác.",
            }

        # Step 3b: Relevance gate — check if top chunks are actually relevant
        RELEVANCE_THRESHOLDS = {
            "specific_event": 2.0,   # Must match title or slug (not just body)
            "broad_topic": 1.0,
            "time_period": 0.5,
            "grade_based": 0.5,
        }
        strategy = (intent or {}).get("search_strategy", "specific_event")
        min_score = RELEVANCE_THRESHOLDS.get(strategy, 1.0)
        top_score = chunks[0].score if chunks else 0

        logger.info("[ORCH] Relevance check: strategy=%s top_score=%.2f min_score=%.2f", strategy, top_score, min_score)

        if top_score < min_score:
            logger.warning("[ORCH] Top score %.2f < threshold %.2f — returning no_data", top_score, min_score)
            await self.page_manager.finish_request(request_id, "no_data", failure_reason=f"Score quá thấp ({top_score:.1f} < {min_score:.1f})")
            await self.db.commit()
            return {
                "status": "no_data",
                "detail": "Tìm thấy một số tài liệu nhưng không đủ liên quan để tạo trang chi tiết. Hãy thử với sự kiện cụ thể hơn.",
            }

        # Step 3c: Query-term coverage check. Generic words like "trận/chiến"
        # are ignored, but distinctive terms from the user's query must match.
        missing_query_terms = _missing_required_query_terms(query, chunks)
        if missing_query_terms and strategy in {"specific_event", "broad_topic"}:
            logger.warning("[ORCH] Query terms not found in chunks — returning no_data. Missing: %s", missing_query_terms)
            await self.page_manager.finish_request(request_id, "no_data", failure_reason=f"Missing query terms: {missing_query_terms}")
            await self.db.commit()
            return {
                "status": "no_data",
                "detail": f"Không tìm thấy thông tin về '{', '.join(missing_query_terms)}' trong kho sử liệu. Hãy thử với sự kiện lịch sử Việt Nam.",
            }

        # Step 3d: Keyword coverage check — verify ALL keywords appear in chunks
        intent_keywords = (intent or {}).get("keywords") or []
        if len(intent_keywords) >= 2 and strategy in {"specific_event", "broad_topic"}:
            missing = _missing_intent_keywords(intent_keywords, chunks)
            logger.info(
                "[ORCH] Keyword coverage: %d/%d matched, missing=%s",
                len(intent_keywords) - len(missing), len(intent_keywords), missing,
            )
            if missing:
                logger.warning("[ORCH] Keywords not found in chunks — returning no_data. Missing: %s", missing)
                await self.page_manager.finish_request(request_id, "no_data", failure_reason=f"Missing keywords: {missing}")
                await self.db.commit()
                return {
                    "status": "no_data",
                    "detail": f"Không tìm thấy thông tin về '{', '.join(missing)}' trong kho sử liệu. Hãy thử với sự kiện lịch sử Việt Nam.",
                }

        # ── Release DB connection back to pool ────────────────────────
        # Steps 4-5 (LLM transform + image generation) don't need DB
        # but can take 30-120s. After commit(), SQLAlchemy 2.0 returns
        # the underlying connection to the pool (lazy checkout).
        # Session remains valid and auto-reconnects for the final save.
        await self.db.commit()
        logger.info("[ORCH] DB committed — connection returned to pool before LLM + image gen")

        # Step 4: Generate payload based on template (no DB needed)
        if is_era_timeline:
            logger.info("[ORCH] Calling payload_from_era_timeline with %d chunks", len(chunks))
            payload = await payload_from_era_timeline(query, chunks, template, intent)
        else:
            logger.info("[ORCH] Calling payload_from_research with %d chunks", len(chunks))
            payload = await payload_from_research(query, chunks, template)
        logger.info("[ORCH] payload returned title=%r template=%r", payload.get("title"), template)

        logger.info("[ORCH] Calling generate_event_images for payload (sync_hero_only=True)")
        payload = await generate_event_images(payload, sync_hero_only=True)

        # Step 6: Save — session auto-reconnects on next query
        page = await self.page_manager.save_story_event_page(
            user_id=user_id,
            title=payload["title"],
            flow_type="system_data",
            source_mode="research",
            template=template,
            render_payload=payload,
            parsed_content_json={"query": query, "chunkIds": [str(chunk.id) for chunk in chunks]},
            sources=payload.get("citations", []),
            request_id=request_id,
        )

        # Trigger background task to generate the remaining images
        import asyncio
        asyncio.create_task(
            background_generate_remaining_images(
                page_id=page["id"],
                user_id=user_id,
                payload=payload,
                query=query,
                chunk_ids=[str(chunk.id) for chunk in chunks],
                citations=payload.get("citations", []),
                request_id=request_id,
                template=template,
            )
        )

        return page

    async def create(self, content: str, template: str, user_id: UUID) -> dict:
        if len(content.strip()) < 50:
            raise HTTPException(status_code=400, detail="Nội dung quá ngắn. Tối thiểu 50 ký tự.")

        request_id = await self.page_manager.create_request(
            user_id=user_id,
            flow_type="custom_content",
            intent="parse_and_render",
            template=template,
            input_text=content,
        )
        moderation = moderate_text(content)
        if moderation.status == "rejected":
            payload = story_event_shell("Nội dung bị từ chối", template, "custom_content", "creator")
            payload["moderation"] = {"status": "rejected", "reason": moderation.reason}
            page = await self.page_manager.save_story_event_page(
                user_id=user_id,
                title="Nội dung bị từ chối",
                flow_type="custom_content",
                source_mode="creator",
                template=template,
                render_payload=payload,
                parsed_content_json={"inputLength": len(content)},
                request_id=request_id,
                status="rejected",
            )
            return {"status": "rejected", "id": page.get("id"), "moderation": payload["moderation"]}

        parsed = parse_creator_content(content, template)
        coverage = check_story_event_coverage(parsed, template)
        if coverage["missing"]:
            payload = story_event_shell(parsed["title"], template, "custom_content", "creator", parsed["summary"])
            payload["coverageReport"] = coverage
            payload["moderation"] = {"status": "approved", "reason": None}
            page = await self.page_manager.save_pending_page(
                user_id=user_id,
                title=parsed["title"],
                template=template,
                render_payload=payload,
                parsed_content_json={"parsed": parsed, "coverageReport": coverage},
                request_id=request_id,
            )
            return {
                "status": "needs_user_confirmation",
                "id": page.get("id"),
                "coverageReport": coverage,
                "moderation": payload["moderation"],
            }

        payload = payload_from_creator(parsed, template, coverage)
        return await self.page_manager.save_story_event_page(
            user_id=user_id,
            title=payload["title"],
            flow_type="custom_content",
            source_mode="creator",
            template=template,
            render_payload=payload,
            parsed_content_json={"parsed": parsed, "coverageReport": coverage},
            request_id=request_id,
        )

    async def confirm_missing(self, page_id: UUID, user_id: UUID) -> dict:
        context = await self.page_manager.get_pending_context(page_id, user_id)
        if context is None:
            raise HTTPException(status_code=404, detail="Pending page not found")

        # parsed_content = context["parsed_content_json"] or {}
        # parsed = parsed_content.get("parsed") or {}
        # coverage = accepted_coverage_report(parsed_content.get("coverageReport") or {})
        # payload = payload_from_creator(parsed, context["template_key"] or "universal", coverage)
        # return await self.page_manager.save_story_event_page(
        #     user_id=user_id,
        #     title=payload["title"],
        #     flow_type="custom_content",
        #     source_mode="creator",
        #     template=context["template_key"] or "universal",
        #     render_payload=payload,
        #     parsed_content_json={"parsed": parsed, "coverageReport": coverage},
        #     request_id=context["request_id"],
        #     page_id=page_id,
        # )

        parsed_content = context["parsed_content_json"] or {}
        parsed = parsed_content.get("parsed") or {}
        coverage = accepted_coverage_report(parsed_content.get("coverageReport") or {})
        payload = payload_from_creator(parsed, context["template_key"] or "universal", coverage)
        return await self.page_manager.save_story_event_page(
            user_id=user_id,
            title=payload["title"],
            flow_type="custom_content",
            source_mode="creator",
            template=context["template_key"] or "universal",
            render_payload=payload,
            parsed_content_json={"parsed": parsed, "coverageReport": coverage},
            request_id=context["request_id"],
            page_id=page_id,
        )


async def background_generate_remaining_images(
    page_id: UUID,
    user_id: UUID,
    payload: dict,
    query: str,
    chunk_ids: list[str],
    citations: list[dict],
    request_id: UUID | None,
    template: str,
):
    import logging
    logger = logging.getLogger("app.generation.background_task")
    logger.info("[BG-IMG] Starting background image generation for page_id=%s", page_id)
    try:
        # Generate the remaining images in the background (non-hero)
        updated_payload = await generate_event_images(payload, sync_hero_only=False)

        # Get a fresh database session to prevent session close conflicts
        from common.db.session import async_session
        from app.workspace.page_manager import PageManager

        async with async_session() as session:
            page_manager = PageManager(session)
            await page_manager.save_story_event_page(
                user_id=user_id,
                title=updated_payload["title"],
                flow_type="system_data",
                source_mode="research",
                template=template,
                render_payload=updated_payload,
                parsed_content_json={"query": query, "chunkIds": chunk_ids},
                sources=citations,
                request_id=request_id,
                page_id=page_id,  # Updates the page with new version and assets
            )
        logger.info("[BG-IMG] Background image generation successfully updated for page_id=%s", page_id)
    except Exception as exc:
        logger.error("[BG-IMG] Background image generation failed for page_id=%s: %s", page_id, exc, exc_info=True)
