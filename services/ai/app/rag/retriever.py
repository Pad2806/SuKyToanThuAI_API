import hashlib
import json
import logging
from dataclasses import asdict, dataclass

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from common.redis.client import get_redis_client

_KEYWORD_STOPWORDS = {
    "ai",
    "bài",
    "cho",
    "chiến",
    "chống",
    "cuộc",
    "của",
    "lịch",
    "một",
    "sử",
    "tắt",
    "tạo",
    "tóm",
    "trang",
    "về",
}


@dataclass
class ChunkResult:
    id: str
    title: str
    content: str
    event_slugs: list[str]
    score: float


def _expand_grade_filters(grade_filter: str | None) -> list[str]:
    if not grade_filter:
        return []

    grade = grade_filter.strip()
    grade_lower = grade.lower()
    filters = [grade]

    if grade_lower.startswith("lớp "):
        grade_number = grade_lower.removeprefix("lớp ").strip()
        filters.append(grade_number)
    elif grade.isdigit():
        grade_number = grade
        filters.append(f"lớp {grade}")
    else:
        grade_number = ""

    if grade_upper := {"TH": range(1, 6), "THCS": range(6, 10), "THPT": range(10, 13)}.get(grade.upper()):
        filters.extend(f"lớp {value}" for value in grade_upper)

    return list(dict.fromkeys(filters))


def _add_grade_condition(conditions: list[str], params: dict, grade_filter: str | None) -> None:
    grade_filters = _expand_grade_filters(grade_filter)
    if not grade_filters:
        return

    grade_conditions = []
    for index, grade in enumerate(grade_filters):
        param = f"grade{index}"
        params[param] = grade
        grade_conditions.append(
            f"EXISTS (SELECT 1 FROM unnest(grade_tags) AS grade_tag WHERE lower(grade_tag) = lower(:{param}))"
        )
    conditions.append(f"({' OR '.join(grade_conditions)})")


def _keyword_terms(keyword: str) -> list[str]:
    import re as _re

    words = _re.findall(r"[\w]+", keyword.lower(), _re.UNICODE)
    return [word for word in words if len(word) >= 3 and word not in _KEYWORD_STOPWORDS]


def _searchable_text_sql() -> str:
    return (
        "concat_ws(' ', title, summary, body, "
        "array_to_string(keywords, ' '), array_to_string(event_slugs, ' '))"
    )


def _add_keyword_conditions(
    conditions: list[str],
    params: dict,
    keywords: list[str],
    param_prefix: str = "kw",
) -> None:
    searchable = _searchable_text_sql()
    keyword_conditions = []
    for index, keyword in enumerate(keywords):
        exact_param = f"{param_prefix}{index}"
        params[exact_param] = f"%{keyword}%"
        exact_match = (
            f"(title ILIKE :{exact_param} OR summary ILIKE :{exact_param} OR body ILIKE :{exact_param} "
            f"OR array_to_string(keywords, ',') ILIKE :{exact_param} "
            f"OR array_to_string(event_slugs, ',') ILIKE :{exact_param})"
        )

        term_matches = []
        for term_index, term in enumerate(_keyword_terms(keyword)):
            term_param = f"{param_prefix}{index}t{term_index}"
            params[term_param] = f"%{term}%"
            term_matches.append(f"{searchable} ILIKE :{term_param}")

        if term_matches:
            keyword_conditions.append(f"({exact_match} OR ({' AND '.join(term_matches)}))")
        else:
            keyword_conditions.append(exact_match)

    if keyword_conditions:
        conditions.append(f"({' OR '.join(keyword_conditions)})")


async def retrieve(query: str, db: AsyncSession, limit: int = 5, intent: dict | None = None) -> list[ChunkResult]:
    """
    Retrieve relevant chunks from official_text_units.
    If `intent` is provided (from LLM extraction), use structured filters.
    Otherwise, fall back to basic full-text + ILIKE search.
    """
    logger.info("[RAG] retrieve() | query=%r | limit=%d | has_intent=%s", query, limit, intent is not None)

    # Cache key MUST include intent to avoid cross-contamination
    intent_hash = ""
    if intent:
        intent_str = json.dumps(intent, sort_keys=True, ensure_ascii=False)
        intent_hash = hashlib.md5(intent_str.encode('utf-8')).hexdigest()[:8]
    cache_key = f"rag:query:{hashlib.md5(query.encode('utf-8')).hexdigest()}:{limit}:{intent_hash}"
    cached = await _cache_get(cache_key)
    if cached:
        logger.info("[RAG] Cache HIT — %d chunks", len(cached))
        return [ChunkResult(**item) for item in cached]

    if intent:
        rows = await _search_with_intent(db, intent, limit)
    else:
        rows = await _search_fallback(db, query, limit)

    chunks = [
        ChunkResult(
            id=row["id"],
            title=row["title"],
            content=row["body"],
            event_slugs=list(row["event_slugs"] or []),
            score=float(row["score"] or 0),
        )
        for row in rows
    ]

    # Filter out low-relevance chunks to prevent cross-event contamination
    if chunks:
        # Absolute minimum: body-only matches (score ≤ 0.3) are NOT relevant
        MIN_RELEVANCE_SCORE = 0.5
        before_abs = len(chunks)
        chunks = [c for c in chunks if c.score >= MIN_RELEVANCE_SCORE]
        if len(chunks) < before_abs:
            logger.info("[RAG] Absolute filter removed %d chunks (score < %.1f)", before_abs - len(chunks), MIN_RELEVANCE_SCORE)

        # Relative threshold: drop anything below 50% of top score
        if chunks:
            top_score = chunks[0].score
            if top_score > 0:
                threshold = top_score * 0.5
                before_rel = len(chunks)
                chunks = [c for c in chunks if c.score >= threshold]
                if len(chunks) < before_rel:
                    logger.info("[RAG] Relative filter removed %d chunks (threshold=%.1f)", before_rel - len(chunks), threshold)

    logger.info("[RAG] Returning %d chunks", len(chunks))
    await _cache_set(cache_key, [asdict(item) for item in chunks])
    return chunks


# ── Century term expansion ─────────────────────────────────────
# LLM may return "thế kỷ 18" but DB stores "thế kỉ XVIII".
# Expand to cover: kỉ/kỷ variants, Arabic/Roman numerals, and
# representative years for each century.
_ARABIC_TO_ROMAN = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
    6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
    11: "XI", 12: "XII", 13: "XIII", 14: "XIV", 15: "XV",
    16: "XVI", 17: "XVII", 18: "XVIII", 19: "XIX", 20: "XX",
    21: "XXI",
}

_CENTURY_REPRESENTATIVE_YEARS: dict[int, list[str]] = {
    1:  ["40", "43"],
    2:  ["248"],
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
    19: ["1802", "1858", "1884"],
    20: ["1930", "1945", "1954", "1975"],
    21: ["1986", "2000"],
}


def _expand_year_terms(year_terms: list[str]) -> list[str]:
    """Expand LLM year_terms into all variant forms that may appear in DB text.

    For a century term like "thế kỷ 18", generates:
      - thế kỉ XVIII, thế kỷ XVIII  (Roman numeral + both ỉ/ỷ)
      - thế kỉ 18, thế kỷ 18        (Arabic numeral + both ỉ/ỷ)
      - 1771, 1789, 1802             (representative years)
    """
    import re as _re

    expanded: list[str] = []
    seen: set[str] = set()

    def _add(term: str) -> None:
        if term not in seen:
            seen.add(term)
            expanded.append(term)

    for yt in year_terms:
        # Check if this is a century term like "thế kỷ 18" or "thế kỉ XIX"
        m = _re.match(
            r"thế\s*k[ỷỉ]\s*(\d+|[IVXLCDM]+)",
            yt.strip(),
            _re.IGNORECASE,
        )
        if m:
            raw_num = m.group(1).strip()
            # Determine century number
            if raw_num.isdigit():
                century = int(raw_num)
            else:
                # Roman to Arabic (reverse lookup)
                century = next(
                    (k for k, v in _ARABIC_TO_ROMAN.items() if v == raw_num.upper()),
                    None,
                )
            if century and 1 <= century <= 21:
                roman = _ARABIC_TO_ROMAN.get(century, str(century))
                arabic = str(century)
                # All spelling variants
                _add(f"thế kỉ {roman}")
                _add(f"thế kỷ {roman}")
                _add(f"thế kỉ {arabic}")
                _add(f"thế kỷ {arabic}")
                # Representative years for this century
                for yr in _CENTURY_REPRESENTATIVE_YEARS.get(century, []):
                    _add(yr)
                continue

        # Not a century term — keep as-is
        _add(yt)

    return expanded


async def _search_with_intent(db: AsyncSession, intent: dict, limit: int) -> list:
    """Build SQL from LLM-extracted intent."""
    strategy = intent.get("search_strategy", "specific_event")
    keywords = intent.get("keywords") or []
    grade_filter = intent.get("grade_filter")
    year_terms = intent.get("year_terms") or []

    logger.info("[RAG] Strategy=%s | keywords=%s | grade=%s | years=%s", strategy, keywords, grade_filter, year_terms)

    conditions = ["status = 'published'"]
    params: dict = {"limit": limit}

    if strategy == "grade_based" and grade_filter:
        # Filter by grade_tags array
        _add_grade_condition(conditions, params, grade_filter)
        logger.info("[RAG] Adding grade filter: %s expanded=%s", grade_filter, _expand_grade_filters(grade_filter))
        # Also add keyword filter if present (e.g. "cách mạng tháng 8 lớp 12")
        if keywords:
            _add_keyword_conditions(conditions, params, keywords)
            logger.info("[RAG] Adding keyword filter within grade: %s", keywords)

    elif strategy == "time_period" and year_terms:
        # Expand century terms into all DB-matching variants
        search_terms = _expand_year_terms(year_terms)
        logger.info("[RAG] Expanded year_terms %s -> %s", year_terms, search_terms)
        # Search expanded terms in body + title
        year_conds = []
        for i, yt in enumerate(search_terms):
            p = f"yt{i}"
            params[p] = f"%{yt}%"
            year_conds.append(f"(body ILIKE :{p} OR title ILIKE :{p})")
        conditions.append(f"({' OR '.join(year_conds)})")
        logger.info("[RAG] Adding year filter: %d terms", len(search_terms))

    elif keywords:
        # Search keywords across all text columns
        _add_keyword_conditions(conditions, params, keywords)

    # Also add grade filter even for non-grade strategies if provided
    if strategy != "grade_based" and grade_filter:
        _add_grade_condition(conditions, params, grade_filter)

    # Build score expression — heavily favor title & slug matches over body
    score_parts = []
    searchable = _searchable_text_sql()
    for i, kw in enumerate(keywords):
        p = f"kw{i}"
        if p in params:
            # Title match = strongest signal (exact topic match)
            score_parts.append(f"CASE WHEN title ILIKE :{p} THEN 5.0 ELSE 0 END")
            # Event slugs / keywords = strong signal (curated metadata)
            score_parts.append(f"CASE WHEN array_to_string(event_slugs, ',') ILIKE :{p} THEN 3.0 ELSE 0 END")
            score_parts.append(f"CASE WHEN array_to_string(keywords, ',') ILIKE :{p} THEN 3.0 ELSE 0 END")
            # Summary match = moderate signal
            score_parts.append(f"CASE WHEN summary ILIKE :{p} THEN 1.0 ELSE 0 END")
            # Body match = weak signal (generic words match too many docs)
            score_parts.append(f"CASE WHEN body ILIKE :{p} THEN 0.3 ELSE 0 END")
            term_conditions = []
            for term_index, _term in enumerate(_keyword_terms(kw)):
                term_param = f"kw{i}t{term_index}"
                if term_param in params:
                    term_conditions.append(f"{searchable} ILIKE :{term_param}")
            if term_conditions:
                score_parts.append(f"CASE WHEN {' AND '.join(term_conditions)} THEN 1.5 ELSE 0 END")

    if not score_parts:
        if strategy in {"grade_based", "time_period"}:
            # For grade queries without keywords, base score = 1
            score_parts = ["1"]
        else:
            score_parts = ["0"]

    score_expr = " + ".join(score_parts)
    where_clause = " AND ".join(conditions)
    order_clause = "score DESC, title ASC"
    if strategy == "grade_based":
        order_clause = (
            "COALESCE(NULLIF(substring(id from 'CH([0-9]+)'), '')::int, 999), "
            "COALESCE(NULLIF(substring(id from 'B([0-9]+)'), '')::int, 999), "
            "score DESC, title ASC"
        )

    sql = f"""
        SELECT id, title, body, event_slugs,
               ({score_expr}) AS score
        FROM public.official_text_units
        WHERE {where_clause}
        ORDER BY {order_clause}
        LIMIT :limit
    """

    logger.info("[RAG] SQL WHERE: %s", where_clause)

    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
        logger.info("[RAG] Intent search returned %d rows", len(rows))
        for i, row in enumerate(rows):
            logger.info("[RAG]   row[%d]: title=%r score=%s", i, row["title"], row["score"])
        return rows
    except Exception as e:
        logger.error("[RAG] Intent search FAILED: %s", e, exc_info=True)
        return []


async def _search_fallback(db: AsyncSession, query: str, limit: int) -> list:
    """Fallback: split query into words, match ANY word across all text columns."""
    import re as _re
    words = [w for w in _re.findall(r"[\w]+", query.lower(), _re.UNICODE) if len(w) >= 2]
    if not words:
        return []

    logger.info("[RAG] Fallback search with %d words: %s", len(words), words)

    # Build per-word ILIKE (OR between words)
    ilike_parts = []
    params: dict = {"limit": limit}
    for i, w in enumerate(words):
        p = f"fw{i}"
        params[p] = f"%{w}%"
        ilike_parts.append(f"(title ILIKE :{p} OR summary ILIKE :{p} OR body ILIKE :{p})")

    where_or = " OR ".join(ilike_parts)

    # Score — title match much heavier than body match
    score_parts = []
    for i, w in enumerate(words):
        p = f"fw{i}"
        score_parts.append(f"CASE WHEN title ILIKE :{p} THEN 5 ELSE 0 END")
        score_parts.append(f"CASE WHEN summary ILIKE :{p} THEN 2 ELSE 0 END")
        score_parts.append(f"CASE WHEN body ILIKE :{p} THEN 1 ELSE 0 END")
    score_expr = " + ".join(score_parts)

    sql = f"""
        SELECT id, title, body, event_slugs, ({score_expr}) AS score
        FROM public.official_text_units
        WHERE status = 'published' AND ({where_or})
        ORDER BY score DESC, title ASC
        LIMIT :limit
    """

    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
        logger.info("[RAG] Fallback returned %d rows", len(rows))
        for i, row in enumerate(rows):
            logger.info("[RAG]   row[%d]: title=%r score=%s", i, row["title"], row["score"])
        return rows
    except Exception as e:
        logger.error("[RAG] Fallback search FAILED: %s", e, exc_info=True)
        return []


async def _cache_get(key: str) -> list[dict] | None:
    try:
        raw = await get_redis_client().get(key)
    except Exception:
        return None
    return json.loads(raw) if raw else None


async def _cache_set(key: str, value: list[dict]) -> None:
    try:
        await get_redis_client().setex(key, 3600, json.dumps(value, ensure_ascii=False))
    except Exception:
        return
