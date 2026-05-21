import logging
import re
import threading
from typing import Any, TYPE_CHECKING

from app.config import settings
from app.safety.content_moderation import moderate_image_prompt

if TYPE_CHECKING:
    from app.providers.imagen_client import ImagenClient

logger = logging.getLogger(__name__)

_imagen_client = None
_last_image_model = None
_image_sources: dict[str, dict[str, str | None]] = {}
FALLBACK_IMAGES = [
    "/images/generated/parchment.png",
    "/images/generated/fallback1.jpg",
    "/images/generated/fallback2.png",
    "/images/generated/fallback3.png",
    "/images/generated/fallback4.png",
    "/images/generated/fallback5.png",
    "/images/generated/fallback6.png",
    "/images/generated/fallback7.png",
]
DEFAULT_IMAGE = "/images/generated/parchment.png"

def get_random_fallback_image() -> str:
    import random
    num = random.randint(1, 7)
    ext = "jpg" if num == 1 else "png"
    return f"/images/generated/fallback{num}.{ext}"

# ── Shared quota-exhaustion flag ─────────────────────────────────
# When ANY provider hits 429, this flag is set so all pending/future
# image tasks skip API calls immediately instead of hammering providers.
_quota_flag = threading.Event()
_quota_error_msg: str | None = None


def _is_any_quota_hit() -> bool:
    return _quota_flag.is_set()


def _set_quota_hit(error_msg: str) -> None:
    global _quota_error_msg
    _quota_error_msg = error_msg
    _quota_flag.set()
    logger.warning("[IMG] QUOTA FLAG SET — all remaining images will use fallback. Error: %s", error_msg[:200])


def _reset_quota_flag() -> None:
    global _quota_error_msg
    _quota_error_msg = None
    _quota_flag.clear()


def get_imagen_client() -> "ImagenClient":
    from app.providers.imagen_client import ImagenClient

    global _imagen_client
    if _imagen_client is None:
        _imagen_client = ImagenClient(
            project_id=settings.google_project_id,
            location=settings.google_location,
            model=settings.imagen_model,
            backup_models=settings.imagen_backup_models,
        )
    return _imagen_client


def _get_gemini_image_client():
    if not settings.google_project_id:
        return None
    try:
        from app.providers.vertex_gemini_client import get_vertex_gemini_image_client

        return get_vertex_gemini_image_client()
    except Exception as exc:
        logger.error("[IMG] Gemini image backup unavailable: %s", exc)
        return None


def _get_gemini_studio_image_client():
    if not settings.gemini_studio_api_key:
        return None
    try:
        from app.providers.gemini_studio_image_client import get_gemini_studio_image_client

        return get_gemini_studio_image_client()
    except Exception as exc:
        logger.error("[IMG] Gemini Studio image backup unavailable: %s", exc)
        return None


def _get_image_backup_clients() -> list[Any]:
    clients = []
    providers = [
        provider.strip().lower()
        for provider in settings.image_backup_provider.split(",")
        if provider.strip()
    ]
    for provider in providers:
        if provider == "gemini":
            client = _get_gemini_image_client()
        elif provider == "gemini_studio":
            client = _get_gemini_studio_image_client()
        else:
            logger.warning("[IMG] Unknown image backup provider: %s", provider)
            client = None
        if client:
            clients.append(client)
    return clients


def _get_all_image_providers() -> list[Any]:
    """Return all available image providers for round-robin distribution."""
    providers = []
    imagen = get_imagen_client()
    if imagen.model:
        providers.append(imagen)
    providers.extend(_get_image_backup_clients())
    return providers


def _last_model_name(imagen: "ImagenClient") -> str | None:
    return _last_image_model or getattr(imagen, "last_model_name", None)


def _record_image_source(url: str, provider: str, model: str | None) -> None:
    _image_sources[url] = {"provider": provider, "model": model}


def _image_source(url: str | None) -> dict[str, str | None]:
    if not url:
        return {"provider": None, "model": None}
    return _image_sources.get(url, {"provider": None, "model": None})


# ── Prompt builders ──────────────────────────────────────────────

_STYLE_BASE = (
    "traditional Vietnamese ink wash painting with watercolor accents, "
    "on aged rice paper texture, muted earth tones with selective gold highlights, "
    "cinematic composition, dramatic natural lighting, "
    "historically accurate Vietnamese clothing and architecture, "
    "no text, no watermarks, no graphic violence, no blood"
)

_ERA_HINTS = {
    "dai-viet": "ancient Dai Viet kingdom, wooden palaces, brick citadels",
    "nguyen-mong": "Mongol Yuan dynasty soldiers with leather armor and composite bows",
    "phap": "French colonial era, European military uniforms, Indochina architecture",
    "viet-minh": "Vietnamese resistance fighters, jungle terrain, 1940s-1950s",
    "van-lang": "Bronze Age Vietnam, Dong Son drums, stilt houses, tribal clothing",
}

_PHASE_VISUAL_DIRECTIONS = (
    "phase role: opening campaign or preparation only, before the decisive battle; "
    "visual focus: commanders, terrain, logistics, artillery setup, troops moving into position; "
    "camera: wide establishing shot from a high diagonal angle; "
    "composition: landscape route and staging area dominate, no victory scene",
    "phase role: main offensive action only, not preparation and not final capture; "
    "visual focus: active assault, crossing, bombardment, infantry advance, or breakthrough moment; "
    "camera: medium action shot at human eye level; "
    "composition: opposing forces converge across the center with strong motion",
    "phase role: final result only, after the breakthrough; "
    "visual focus: captured objective, surrendered command post, raised flag, or troops entering the final target; "
    "camera: low dramatic foreground angle; "
    "composition: victory/result symbol dominates foreground, battlefield receding behind",
)

_ERA_VISUAL_DIRECTIONS = (
    "unique timeline image, visual focus: settlement and daily life; "
    "camera: elevated wide landscape; composition: river or road leading line",
    "unique timeline image, visual focus: royal court and architecture; "
    "camera: symmetrical frontal view; composition: palace gate or citadel dominates",
    "unique timeline image, visual focus: military movement or battle strategy; "
    "camera: dynamic oblique view; composition: formations crossing the frame",
    "unique timeline image, visual focus: scholarship, reform, or diplomacy; "
    "camera: intimate interior medium shot; composition: figures around documents",
    "unique timeline image, visual focus: social change and public life; "
    "camera: street-level documentary view; composition: layered crowd and buildings",
)


def _coerce_year(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if not match:
            return None
        year = int(match.group())
        ancient_marker = value.lower()
        if "tcn" in ancient_marker or "bc" in ancient_marker or "bce" in ancient_marker:
            return -year
        return year
    return None


def _detect_era(event: dict[str, Any]) -> str:
    """Detect historical era from event data for style hints."""
    year = _coerce_year(event.get("year"))
    sides = [c.get("side", "") for c in event.get("characters", [])]

    for side in sides:
        if side in _ERA_HINTS:
            return _ERA_HINTS[side]

    if year:
        if year < 0 or year < 200:
            return _ERA_HINTS["van-lang"]
        if year < 1400:
            return _ERA_HINTS["dai-viet"]
        if 1858 <= year <= 1945:
            return _ERA_HINTS["phap"]
        if 1945 <= year <= 1975:
            return _ERA_HINTS["viet-minh"]

    return "ancient Vietnam, traditional setting"


def build_hero_prompt(event: dict[str, Any]) -> str:
    """Build detailed hero image prompt from full event context."""
    title = event.get("title", "")
    summary = event.get("summary", "")
    location = event.get("location", "")
    year = event.get("year", "")
    actors = ", ".join(event.get("actors", [])[:3])
    result = event.get("result", "")
    era_hint = _detect_era(event)

    scene_details = []
    if location:
        scene_details.append(f"setting: {location}")
    if year:
        scene_details.append(f"year {year}")
    if actors:
        scene_details.append(f"featuring {actors}")
    if result:
        scene_details.append(f"outcome: {result}")

    scene = ", ".join(scene_details)

    return (
        f"{_STYLE_BASE}, {era_hint}. "
        f"Scene: {title}. {summary[:150]}. "
        f"{scene}. "
        f"Wide panoramic landscape shot, establishing shot atmosphere."
    )


def build_climax_prompt(event: dict[str, Any]) -> str:
    """Build climax scene prompt with dramatic tension."""
    title = event.get("title", "")
    climax = event.get("climaxScene", {})
    phases = climax.get("phases", [])
    era_hint = _detect_era(event)

    # Combine phase descriptions for maximum context
    phase_desc = ". ".join(
        p.get("summary", "") for p in phases[:2] if p.get("summary")
    )
    if not phase_desc:
        phase_desc = event.get("summary", title)

    return (
        f"Tactical military campaign map for an interactive history page, "
        f"top-down bird's eye view, aged parchment paper texture, ink and watercolor cartography style, "
        f"terrain features with mountains, roads, rivers, forests, cities and defensive lines drawn as map symbols, "
        f"troop movement arrows, attack routes, encirclement marks, objective markers and front lines, "
        f"compass rose, map legend shapes without readable text, muted earth tones with red and gold strategic annotations, "
        f"no soldiers, no close-up tanks, no cinematic battlefield scene, no readable text, no watermarks. "
        f"Operational map of: {title}. {phase_desc[:240]}. "
        f"{era_hint}."
    )


def build_phase_prompt(event: dict[str, Any], phase: dict[str, Any], phase_index: int) -> str:
    """Build image prompt for a specific climax phase.
    Prefers AI-generated image_prompt for maximum context accuracy.
    """
    era_hint = _detect_era(event)
    ai_prompt = phase.get("image_prompt")
    visual_direction = _PHASE_VISUAL_DIRECTIONS[phase_index % len(_PHASE_VISUAL_DIRECTIONS)]
    title = event.get("title", "")
    label = phase.get("label", f"Phase {phase_index + 1}")
    description = phase.get("description", phase.get("summary", ""))
    all_phases = event.get("climaxScene", {}).get("phases", [])
    other_labels = [
        item.get("label", "")
        for i, item in enumerate(all_phases[:3])
        if i != phase_index and item.get("label")
    ]
    exclusions = ""
    if other_labels:
        exclusions = f" Do not depict these other phases: {', '.join(other_labels)}."
    phase_brief = (
        f"Illustrate PHASE {phase_index + 1} ONLY from {title}: {label}. "
        f"Phase-specific context: {description[:220]}."
    )

    if ai_prompt:
        # AI wrote a context-specific prompt — prepend style base
        return (
            f"{_STYLE_BASE}, {era_hint}. {phase_brief} "
            f"Image details: {ai_prompt}. {visual_direction}. "
            f"Must be visually distinct from the other two phase images. "
            f"Do not reuse the same vehicle pose, tank-front composition, focal subject, "
            f"camera angle, terrain, or background from any other phase image.{exclusions}"
        )

    # Fallback: build from description
    return (
        f"{_STYLE_BASE}, {era_hint}. "
        f"{phase_brief} "
        f"Cinematic dramatic composition, detailed environment, "
        f"{visual_direction}. "
        f"Must be visually distinct from the other two phase images. "
        f"Do not reuse the same vehicle pose, tank-front composition, focal subject, "
        f"camera angle, terrain, or background from any other phase image.{exclusions}"
    )


def build_phase_retry_prompt(event: dict[str, Any], phase: dict[str, Any], phase_index: int) -> str:
    """Build a safer retry prompt when Imagen rejects or fails a detailed phase prompt."""
    era_hint = _detect_era(event)
    visual_direction = _PHASE_VISUAL_DIRECTIONS[phase_index % len(_PHASE_VISUAL_DIRECTIONS)]
    title = event.get("title", "")
    label = phase.get("label", f"Phase {phase_index + 1}")
    summary = phase.get("summary") or phase.get("description") or label
    return (
        f"{_STYLE_BASE}, {era_hint}. "
        f"Symbolic non-graphic historical illustration for PHASE {phase_index + 1} ONLY "
        f"from {title}: {label}. {summary[:180]}. "
        f"{visual_direction}. "
        f"Show strategy, movement, terrain, flags, command decisions, or public outcome. "
        f"No crash, no injury, no close-up weapons, no readable text, no graphic violence."
    )


def build_era_prompt(event: dict[str, Any], era: dict[str, Any], era_index: int = 0) -> str:
    """Build an era-timeline card image prompt, even when LLM omitted image_prompt."""
    era_hint = _detect_era(event)
    ai_prompt = era.get("image_prompt")
    visual_direction = _ERA_VISUAL_DIRECTIONS[era_index % len(_ERA_VISUAL_DIRECTIONS)]
    if ai_prompt:
        return (
            f"{_STYLE_BASE}, {era_hint}. {ai_prompt}. {visual_direction}. "
            f"Do not reuse the same scene, focal subject, camera angle, or composition "
            f"from any other timeline image."
        )

    name = era.get("name") or "Historical era"
    year_range = era.get("yearRange") or era.get("year_range") or ""
    summary = era.get("summary") or event.get("summary") or name
    figures = ", ".join((era.get("keyFigures") or [])[:4])
    events = ", ".join(
        item.get("title", "")
        for item in (era.get("keyEvents") or [])[:4]
        if item.get("title")
    )

    details = []
    if year_range:
        details.append(f"time period {year_range}")
    if figures:
        details.append(f"featuring {figures}")
    if events:
        details.append(f"key events: {events}")

    return (
        f"{_STYLE_BASE}, {era_hint}. "
        f"Scene representing {name}. {summary[:180]}. "
        f"{', '.join(details)}. "
        f"Wide cinematic historical tableau. {visual_direction}. "
        f"Do not reuse the same scene, focal subject, camera angle, or composition "
        f"from any other timeline image."
    )


def build_portrait_prompt(name: str, role: str, side: str, bio: str = "") -> str:
    """Build character portrait prompt with historical accuracy."""
    era_hint = _ERA_HINTS.get(side, "ancient Vietnamese noble")

    bio_snippet = ""
    if bio:
        bio_snippet = f" Background: {bio[:100]}."

    side_desc = {
        "dai-viet": "Vietnamese general/noble wearing traditional áo dài or battle armor with golden dragon motifs",
        "nguyen-mong": "Mongol-Yuan commander wearing leather and fur armor, Mongolian features",
        "phap": "French military officer in colonial uniform with kepi hat",
        "viet-minh": "Vietnamese revolutionary leader in simple khaki uniform",
        "other": "historical Vietnamese figure in period-appropriate clothing",
    }

    clothing = side_desc.get(side, side_desc["other"])

    return (
        f"Portrait painting of {name}, {role}. {clothing}. "
        f"{bio_snippet} "
        f"Dignified three-quarter view pose, sharp facial features, "
        f"traditional Vietnamese ink painting style with watercolor, "
        f"aged paper texture background, warm earth tones, "
        f"cinematic portrait lighting, museum-quality illustration. "
        f"No text, no watermarks."
    )


def build_image_assets(parsed: dict[str, Any], coverage_report: dict[str, Any]) -> list[dict[str, Any]]:
    omitted = set(coverage_report.get("omittedSections") or [])
    if "image" in omitted:
        return []

    title = parsed.get("title") or "Trang lịch sử"
    details = parsed.get("image_details") or parsed.get("summary") or title
    prompt = f"Minh họa lịch sử Việt Nam, {title}. Bối cảnh: {details}. Phong cách cinematic, giáo dục, không bạo lực đồ họa."
    # prompt = (
    #     f"{_STYLE_BASE}. Scene: {title}. {details[:200]}. "
    #     f"Wide panoramic landscape shot."
    # )
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


# ── Generation orchestration ─────────────────────────────────────

def _is_quota_error_str(error: str) -> bool:
    """Check if an error string indicates quota exhaustion."""
    normalized = error.lower()
    return "429" in normalized or "quota" in normalized or "resource_exhausted" in normalized


async def _safe_generate(imagen: "ImagenClient", prompt: str, aspect: str = "16:9") -> str | None:
    """Generate image with error handling, returns URL or None.

    Checks shared quota flag before calling any provider.
    Sets the flag if any provider returns 429.
    """
    global _last_image_model
    _last_image_model = None

    # ── Early exit if quota already exhausted ──
    if _is_any_quota_hit():
        logger.info("[IMG] Skipping — quota flag already set")
        return None

    moderation = moderate_image_prompt(prompt)
    if moderation.status != "approved":
        logger.warning("[IMG] Prompt rejected by moderation: %s", prompt[:80])
        return None
    try:
        logger.warning(
            "[IMG] Calling primary provider=Imagen models=%s aspect=%s",
            ", ".join(getattr(imagen, "model_names", []) or []),
            aspect,
        )
        url = await imagen.generate_image(prompt=prompt, aspect_ratio=aspect)
        if url:
            _last_image_model = getattr(imagen, "last_model_name", None)
            _record_image_source(url, "Imagen", _last_image_model)
            logger.warning("[IMG] Generated with primary provider=Imagen model=%s url=%s", _last_image_model, url)
            return url

        # Primary failed — check if it was a quota error
        primary_error = str(getattr(imagen, "last_error", "") or "")
        if _is_quota_error_str(primary_error):
            logger.warning("[IMG] Primary Imagen quota hit: %s", primary_error[:200])
            # Don't set global flag yet — try backup first
        else:
            logger.warning(
                "[IMG] Primary Imagen returned no image last_model=%s last_error=%s",
                getattr(imagen, "last_model_name", None),
                primary_error,
            )

        # ── Try backup providers ──
        for backup in _get_image_backup_clients():
            if _is_any_quota_hit():
                logger.info("[IMG] Skipping backup — quota flag set by another task")
                return None
            logger.warning(
                "[IMG] Trying image backup provider=%s model=%s",
                backup.__class__.__name__,
                getattr(backup, "model_name", None),
            )
            url = await backup.generate_image(prompt=prompt, aspect_ratio=aspect)
            if url:
                _last_image_model = getattr(backup, "last_model_name", None)
                _record_image_source(url, backup.__class__.__name__, _last_image_model)
                logger.warning(
                    "[IMG] Generated with image backup provider=%s model=%s url=%s",
                    backup.__class__.__name__,
                    _last_image_model,
                    url,
                )
                return url
            # Backup also failed — check if quota error
            backup_error = str(getattr(backup, "last_error", "") or "")
            if _is_quota_error_str(backup_error):
                logger.warning(
                    "[IMG] Backup %s quota hit: %s",
                    backup.__class__.__name__,
                    backup_error[:200],
                )
            else:
                logger.warning(
                    "[IMG] Backup provider failed provider=%s model=%s error=%s",
                    backup.__class__.__name__,
                    getattr(backup, "model_name", None),
                    backup_error,
                )

        # All providers failed — if primary was quota error, set global flag
        if _is_quota_error_str(primary_error):
            _set_quota_hit(primary_error)

        return None
    except Exception as e:
        error_msg = str(e)
        if _is_quota_error_str(error_msg):
            _set_quota_hit(error_msg)
        logger.error("[IMG] Generation failed: %s", e)
        return None


async def _safe_generate_direct(provider: Any, prompt: str, aspect: str = "16:9") -> str | None:
    """Generate image using a SPECIFIC provider (no fallback chain).

    Used in round-robin mode to distribute images across all providers evenly.
    """
    global _last_image_model
    _last_image_model = None

    if _is_any_quota_hit():
        logger.info("[IMG] Skipping — quota flag already set")
        return None

    moderation = moderate_image_prompt(prompt)
    if moderation.status != "approved":
        logger.warning("[IMG] Prompt rejected by moderation: %s", prompt[:80])
        return None

    provider_name = provider.__class__.__name__
    try:
        logger.warning(
            "[IMG] Round-robin calling provider=%s model=%s aspect=%s",
            provider_name,
            getattr(provider, "model_name", getattr(provider, "model", None)),
            aspect,
        )
        url = await provider.generate_image(prompt=prompt, aspect_ratio=aspect)
        if url:
            _last_image_model = getattr(provider, "last_model_name", None)
            _record_image_source(url, provider_name, _last_image_model)
            logger.warning("[IMG] Generated with provider=%s model=%s url=%s", provider_name, _last_image_model, url)
            return url

        error = str(getattr(provider, "last_error", "") or "")
        if _is_quota_error_str(error):
            logger.warning("[IMG] Provider %s quota hit: %s", provider_name, error[:200])
        else:
            logger.warning("[IMG] Provider %s returned no image, error=%s", provider_name, error)
        return None
    except Exception as e:
        error_msg = str(e)
        if _is_quota_error_str(error_msg):
            _set_quota_hit(error_msg)
        logger.error("[IMG] Generation failed provider=%s: %s", provider_name, e)
        return None


def _quota_exceeded(imagen: "ImagenClient") -> bool:
    # Check shared flag first (covers all providers)
    if _is_any_quota_hit():
        return True
    # Fallback: check imagen's last_error
    error = str(getattr(imagen, "last_error", "") or "").lower()
    return "429" in error or "quota" in error or "resource_exhausted" in error


def _skip_remaining_phases(phases: list[dict[str, Any]], start_index: int, error: str | None) -> None:
    for phase in phases[start_index:3]:
        phase.setdefault("image", get_random_fallback_image())
        phase["imageStatus"] = "quota_skipped"
        phase["imageError"] = error
        phase["imageFallback"] = True


def _mark_climax_map_fallback(climax: dict[str, Any], error: str | None, status: str = "quota_skipped") -> None:
    climax["backgroundImage"] = climax.get("backgroundImage") or get_random_fallback_image()
    climax["backgroundImageStatus"] = status
    climax["backgroundImageError"] = error
    climax["backgroundImageFallback"] = True


def _mark_quota_and_stop_remaining_images(event: dict[str, Any], error: str | None) -> None:
    event["image"] = event.get("image") or get_random_fallback_image()
    event["imageStatus"] = "quota_exceeded"
    event["imageError"] = error
    event["imageFallback"] = True

    climax = event.get("climaxScene")
    if isinstance(climax, dict):
        phases = climax.get("phases") or []
        if isinstance(phases, list):
            _skip_remaining_phases(phases, 0, error)
        climax.setdefault("backgroundImagePrompt", build_climax_prompt(event))
        _mark_climax_map_fallback(climax, error)

    for character in event.get("characters") or []:
        if not character.get("portrait"):
            character["portrait"] = get_random_fallback_image()
            character["portraitStatus"] = "quota_skipped"
            character["portraitError"] = error
            character["portraitFallback"] = True

    for era in event.get("eras") or []:
        if not era.get("image"):
            era["image"] = get_random_fallback_image()
            era["imageStatus"] = "quota_skipped"
            era["imageError"] = error
            era["imageFallback"] = True


def _inject_story_images(event: dict[str, Any], image_url: str | None) -> None:
    if not image_url:
        return
    story = event.get("story", {})
    for beat in story.get("beats", []):
        for block in beat.get("blocks", []):
            if block.get("type") == "image" and block.get("image") is None:
                block["image"] = image_url


def _add_image_generation_summary(payload: dict[str, Any]) -> None:
    event = payload.get("eventData", {})
    summary = []
    if event.get("image"):
        summary.append({
            "slot": "hero",
            "url": event.get("image"),
            "status": event.get("imageStatus"),
            "provider": event.get("imageProvider"),
            "model": event.get("imageModel"),
            "error": event.get("imageError"),
        })

    climax = event.get("climaxScene") or {}
    for index, phase in enumerate((climax.get("phases") or [])[:3], start=1):
        summary.append({
            "slot": f"climax.phase.{index}",
            "label": phase.get("label"),
            "url": phase.get("image"),
            "status": phase.get("imageStatus"),
            "provider": phase.get("imageProvider"),
            "model": phase.get("imageModel"),
            "error": phase.get("imageError"),
        })
    if climax.get("backgroundImage"):
        summary.append({
            "slot": "climax.map",
            "url": climax.get("backgroundImage"),
            "status": climax.get("backgroundImageStatus"),
            "provider": climax.get("backgroundImageProvider"),
            "model": climax.get("backgroundImageModel"),
            "error": climax.get("backgroundImageError"),
        })

    for index, character in enumerate(event.get("characters") or [], start=1):
        if character.get("portrait") or character.get("portraitStatus"):
            summary.append({
                "slot": f"character.{index}.portrait",
                "label": character.get("name"),
                "url": character.get("portrait"),
                "status": character.get("portraitStatus"),
                "provider": character.get("portraitProvider"),
                "model": character.get("portraitModel"),
                "error": character.get("portraitError"),
            })

    for index, era in enumerate(event.get("eras") or [], start=1):
        summary.append({
            "slot": f"era.{index}",
            "label": era.get("name") or era.get("title"),
            "url": era.get("image"),
            "status": era.get("imageStatus"),
            "provider": era.get("imageProvider"),
            "model": era.get("imageModel"),
            "error": era.get("imageError"),
        })

    payload["imageGenerationSummary"] = summary


async def generate_event_images(payload: dict[str, Any], sync_hero_only: bool = False) -> dict[str, Any]:
    """Generate images using Vertex AI Imagen and attach to payload.

    Uses asyncio.gather to run independent image generations in parallel,
    reducing total wall time from 120+ seconds (sequential) to ~30-45 seconds.
    """
    import asyncio

    event = payload.get("eventData", {})
    title = event.get("title", "")

    if not settings.google_project_id:
        logger.warning("[IMG] No GOOGLE_PROJECT_ID, skipping image generation")
        return payload

    imagen = get_imagen_client()
    if not imagen.model and not _get_image_backup_clients():
        logger.warning("[IMG] No image generation model initialized, skipping")
        return payload

    logger.info("[IMG] Starting PARALLEL image generation for: %s (sync_hero_only=%s)", title, sync_hero_only)
    # Reset quota flag for this batch — providers may have recovered
    _reset_quota_flag()

    # ── Build all prompts upfront ──────────────────────────────────
    hero_prompt = build_hero_prompt(event)

    climax = event.get("climaxScene")
    phase_prompts: list[tuple[int, dict, str]] = []
    map_prompt: str | None = None
    if climax:
        phases = climax.get("phases", [])
        for i, phase in enumerate(phases[:3]):
            prompt = build_phase_prompt(event, phase, i)
            phase["imageGenerationPrompt"] = prompt
            phase_prompts.append((i, phase, prompt))
        map_prompt = build_climax_prompt(event)
        climax["backgroundImagePrompt"] = map_prompt

    portrait_prompt: str | None = None
    main_char: dict | None = None
    characters = event.get("characters", [])
    if characters:
        main_char = characters[0]
        portrait_prompt = build_portrait_prompt(
            main_char.get("name", ""),
            main_char.get("role", ""),
            main_char.get("side", "other"),
            main_char.get("bio", ""),
        )

    era_prompts: list[tuple[int, dict, str]] = []
    eras = event.get("eras", [])
    for i, era in enumerate(eras):
        era_prompts.append((i, era, build_era_prompt(event, era, i)))

    # ── Fire all image generations concurrently (round-robin) ────────
    # Distribute images across ALL available providers to spread quota evenly.
    _semaphore = asyncio.Semaphore(3)
    tasks: dict[str, asyncio.Task] = {}

    all_providers = _get_all_image_providers()
    provider_count = len(all_providers)
    logger.info(
        "[IMG] Available providers for round-robin: %s",
        [f"{p.__class__.__name__}({getattr(p, 'model_name', getattr(p, 'model', '?'))})" for p in all_providers],
    )

    # Fallback: if no providers available, use old single-provider path
    if provider_count == 0:
        logger.warning("[IMG] No image providers available — using Imagen only")
        all_providers = [imagen]
        provider_count = 1

    task_index = 0  # global counter for round-robin assignment

    async def _gen_rr(prompt: str, provider: Any, aspect: str = "16:9") -> str | None:
        async with _semaphore:
            return await _safe_generate_direct(provider, prompt, aspect)

    # ── Budget: max 6 images total to stay within provider quotas ──
    MAX_GENERATED_IMAGES = 6
    image_budget = MAX_GENERATED_IMAGES

    # Hero (always generated if not already generated)
    hero_already_generated = False
    if event.get("image") and event.get("image") not in FALLBACK_IMAGES and event.get("imageStatus") in {"generated", "generated_retry"}:
        hero_already_generated = True

    if not hero_already_generated:
        provider = all_providers[task_index % provider_count]
        logger.info("[IMG] Hero prompt → %s: %s", provider.__class__.__name__, hero_prompt[:120])
        tasks["hero"] = asyncio.ensure_future(_gen_rr(hero_prompt, provider, "16:9"))
        image_budget -= 1
        task_index += 1
    else:
        logger.info("[IMG] Hero image already generated: %s", event.get("image"))

    if not sync_hero_only:
        # Phases
        for i, phase, prompt in phase_prompts:
            if image_budget <= 0:
                break
            if phase.get("image") and phase.get("image") not in FALLBACK_IMAGES and phase.get("imageStatus") in {"generated", "generated_retry"}:
                logger.info("[IMG] Phase %d already generated, skipping queue", i + 1)
                continue
            provider = all_providers[task_index % provider_count]
            logger.info("[IMG] Phase %d → %s: %s", i + 1, provider.__class__.__name__, prompt[:120])
            tasks[f"phase_{i}"] = asyncio.ensure_future(_gen_rr(prompt, provider, "16:9"))
            image_budget -= 1
            task_index += 1

        # Climax map
        if map_prompt and image_budget > 0:
            if not (climax.get("backgroundImage") and climax.get("backgroundImage") not in FALLBACK_IMAGES and climax.get("backgroundImageStatus") in {"generated"}):
                provider = all_providers[task_index % provider_count]
                logger.info("[IMG] Climax map → %s: %s", provider.__class__.__name__, map_prompt[:120])
                tasks["climax_map"] = asyncio.ensure_future(_gen_rr(map_prompt, provider, "16:9"))
                image_budget -= 1
                task_index += 1
            else:
                logger.info("[IMG] Climax map already generated, skipping queue")

        # Portrait
        if portrait_prompt and image_budget > 0:
            if not (main_char.get("portrait") and main_char.get("portrait") not in FALLBACK_IMAGES and main_char.get("portraitStatus") in {"generated"}):
                provider = all_providers[task_index % provider_count]
                logger.info("[IMG] Portrait → %s: %s", provider.__class__.__name__, portrait_prompt[:120])
                tasks["portrait"] = asyncio.ensure_future(_gen_rr(portrait_prompt, provider, "1:1"))
                image_budget -= 1
                task_index += 1
            else:
                logger.info("[IMG] Portrait already generated, skipping queue")

        # Eras
        for i, era, prompt in era_prompts:
            if image_budget <= 0:
                if not era.get("image"):
                    era["image"] = get_random_fallback_image()
                    era["imageStatus"] = "budget_skipped"
                    era["imageFallback"] = True
                continue
            if era.get("image") and era.get("image") not in FALLBACK_IMAGES and era.get("imageStatus") in {"generated"}:
                logger.info("[IMG] Era %s already generated, skipping queue", era.get("id", "?"))
                continue
            provider = all_providers[task_index % provider_count]
            logger.info("[IMG] Era %s → %s: %s", era.get("id", "?"), provider.__class__.__name__, prompt[:120])
            tasks[f"era_{i}"] = asyncio.ensure_future(_gen_rr(prompt, provider, "16:9"))
            image_budget -= 1
            task_index += 1

    logger.info("[IMG] Total image tasks queued: %d / %d max", len(tasks), MAX_GENERATED_IMAGES)

    # Wait for all tasks to complete
    if tasks:
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        result_map = dict(zip(tasks.keys(), results))
    else:
        result_map = {}

    # ── Assign results back to payload ─────────────────────────────

    # Hero image
    if not hero_already_generated:
        hero_url = result_map.get("hero")
        if isinstance(hero_url, Exception):
            logger.error("[IMG] Hero generation exception: %s", hero_url)
            hero_url = None
        if hero_url:
            source = _image_source(hero_url)
            event["image"] = hero_url
            event["imageStatus"] = "generated"
            event["imageProvider"] = source["provider"]
            event["imageModel"] = source["model"]
        else:
            # Check if quota exceeded — mark all remaining as skipped
            if _quota_exceeded(imagen):
                error = getattr(imagen, "last_error", None)
                logger.warning("[IMG] Quota exceeded on hero image; marking remaining as skipped")
                _mark_quota_and_stop_remaining_images(event, error)
                _inject_story_images(event, event.get("image"))
                _add_image_generation_summary(payload)
                return payload

    # Phase images
    if climax:
        phases = climax.get("phases", [])
        for i, phase in enumerate(phases[:3]):
            key = f"phase_{i}"
            phase_url = result_map.get(key)
            if isinstance(phase_url, Exception):
                logger.error("[IMG] Phase %d generation exception: %s", i + 1, phase_url)
                phase_url = None
            if phase_url:
                source = _image_source(phase_url)
                phase["image"] = phase_url
                phase["imageStatus"] = "generated"
                phase["imageProvider"] = source["provider"]
                phase["imageModel"] = source["model"]
            else:
                if sync_hero_only:
                    if not phase.get("image"):
                        phase["image"] = DEFAULT_IMAGE
                        phase["imageStatus"] = "pending"
                else:
                    if phase.get("imageStatus") in {"generated", "generated_retry"}:
                        continue
                    # Try retry prompt sequentially (only for failed phases, not quota)
                    if not _quota_exceeded(imagen):
                        retry_prompt = build_phase_retry_prompt(event, phase, i)
                        phase["imageRetryPrompt"] = retry_prompt
                        logger.info("[IMG] Phase %d retry prompt: %s", i + 1, retry_prompt[:120])
                        retry_url = await _safe_generate(imagen, retry_prompt, "16:9")
                        if retry_url:
                            source = _image_source(retry_url)
                            phase["image"] = retry_url
                            phase["imageStatus"] = "generated_retry"
                            phase["imageProvider"] = source["provider"]
                            phase["imageModel"] = source["model"]
                        else:
                            phase["image"] = phase.get("image") or get_random_fallback_image()
                            phase["imageStatus"] = "failed"
                            phase["imageError"] = getattr(imagen, "last_error", None)
                            phase["imageFallback"] = True
                    else:
                        error = getattr(imagen, "last_error", None)
                        phase["image"] = phase.get("image") or get_random_fallback_image()
                        phase["imageStatus"] = "quota_exceeded"
                        phase["imageError"] = error
                        phase["imageFallback"] = True

        # Climax map
        map_url = result_map.get("climax_map")
        if isinstance(map_url, Exception):
            logger.error("[IMG] Climax map generation exception: %s", map_url)
            map_url = None
        if map_url:
            source = _image_source(map_url)
            climax["backgroundImage"] = map_url
            climax["backgroundImageStatus"] = "generated"
            climax["backgroundImageProvider"] = source["provider"]
            climax["backgroundImageModel"] = source["model"]
        else:
            if sync_hero_only:
                if not climax.get("backgroundImage"):
                    climax["backgroundImage"] = DEFAULT_IMAGE
                    climax["backgroundImageStatus"] = "pending"
            else:
                if climax.get("backgroundImageStatus") not in {"generated"}:
                    error = getattr(imagen, "last_error", None)
                    status = "quota_exceeded" if _quota_exceeded(imagen) else "failed"
                    _mark_climax_map_fallback(climax, error, status)

    # Portrait
    if main_char and portrait_prompt:
        portrait_url = result_map.get("portrait")
        if isinstance(portrait_url, Exception):
            logger.error("[IMG] Portrait generation exception: %s", portrait_url)
            portrait_url = None
        if portrait_url:
            source = _image_source(portrait_url)
            main_char["portrait"] = portrait_url
            main_char["portraitStatus"] = "generated"
            main_char["portraitProvider"] = source["provider"]
            main_char["portraitModel"] = source["model"]
        else:
            if sync_hero_only:
                if not main_char.get("portrait"):
                    main_char["portrait"] = DEFAULT_IMAGE
                    main_char["portraitStatus"] = "pending"
            else:
                if main_char.get("portraitStatus") not in {"generated"}:
                    main_char["portrait"] = get_random_fallback_image()
                    main_char["portraitStatus"] = "failed"
                    main_char["portraitError"] = getattr(imagen, "last_error", None)
                    main_char["portraitFallback"] = True

    # Era images
    for i, era, _ in era_prompts:
        key = f"era_{i}"
        era_url = result_map.get(key)
        if isinstance(era_url, Exception):
            logger.error("[IMG] Era %s generation exception: %s", era.get("id", "?"), era_url)
            era_url = None
        if era_url:
            source = _image_source(era_url)
            era["image"] = era_url
            era["imageStatus"] = "generated"
            era["imageProvider"] = source["provider"]
            era["imageModel"] = source["model"]
        elif not era.get("image") or era.get("imageStatus") == "pending":
            if sync_hero_only:
                era["image"] = DEFAULT_IMAGE
                era["imageStatus"] = "pending"
            else:
                era["image"] = get_random_fallback_image()
                era["imageStatus"] = "failed"
                era["imageError"] = getattr(imagen, "last_error", None)
                era["imageFallback"] = True

    # Inject hero image into story beat image blocks with null
    _inject_story_images(event, event.get("image"))
    _add_image_generation_summary(payload)

    logger.info("[IMG] PARALLEL image generation complete for: %s (sync_hero_only=%s)", title, sync_hero_only)
    return payload
