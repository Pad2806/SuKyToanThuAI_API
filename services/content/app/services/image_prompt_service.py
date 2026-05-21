from typing import Any

from app.services.image_prompt_context import build_slot_context

UNSAFE_TERMS = {"nude", "porn", "sexual", "bloodbath"}
DEFAULT_LOCATION = "Việt Nam"
BASE_STYLE_PROMPT = (
    "Vietnamese historical epic illustration, cinematic comic-book style, hand-painted look, "
    "slightly stylized characters, not photorealistic, no real-person likeness, "
    "no detailed realistic faces, dramatic lighting, ancient Vietnam atmosphere, parchment and ink texture, "
    "rich but muted colors, period-appropriate Vietnamese historical costume and terrain, "
    "high detail environment, no modern objects"
)
TEXT_RULE = (
    "Prefer no text inside the image. If text appears, it must be short, clear Vietnamese text, "
    "correctly spelled, no gibberish, no broken letters."
)
AVOID_RULE = (
    "Avoid photorealism, realistic portraits, real-person likeness, detailed faces, close-up faces, "
    "modern objects, unreadable text, Chinese/Japanese fantasy armor, anime school style, horror gore, and excessive blood."
)
BASE_NEGATIVE_PROMPT = (
    "photorealistic, realistic portrait, real person likeness, detailed face, celebrity likeness, "
    "modern clothing, modern weapons, guns, cars, skyscrapers, distorted Vietnamese text, gibberish text, "
    "unreadable letters, Chinese fantasy armor, Japanese fantasy armor, anime school style, horror gore, "
    "excessive blood, watermark, logo, speech bubbles, low quality, blurry"
)

def build_prompt(event: dict[str, Any], slot: dict[str, Any]) -> str:
    return build_image_request(event, slot)["prompt"]

def build_image_request(event: dict[str, Any], slot: dict[str, Any], prompt_override: str | None = None) -> dict[str, Any]:
    if prompt_override:
        return _request(prompt_override, _people_profile())
    slot_key = str(slot.get("slot_key") or "hero")
    return _request(_build_prompt(event, slot), _profile_for_slot(slot_key))

def build_image_request_attempts(event: dict[str, Any], slot: dict[str, Any]) -> list[dict[str, Any]]:
    primary = build_image_request(event, slot)
    return [primary, *(_fallback_request(event, slot, level) for level in (1, 2, 3))]

def is_people_safety_block(error: Exception | str) -> bool:
    message = str(error).lower()
    safety_terms = ("safety", "filtered", "people/face", "face generation", "rai", "no bytes were found")
    return any(term in message for term in safety_terms) and not any(term in message for term in ("quota", "billing"))

def moderate_prompt(prompt: str) -> str | None:
    lowered = prompt.lower()
    if any(term in lowered for term in UNSAFE_TERMS):
        return "Prompt contains unsafe image content"
    return None

def _build_prompt(event: dict[str, Any], slot: dict[str, Any]) -> str:
    slot_key = str(slot.get("slot_key") or "hero")
    slot_label = str(slot.get("slot_label") or slot_key)
    title = _clean(event.get("title") or "Sự kiện lịch sử Việt Nam")
    summary = _clean(event.get("summary") or title, 420)
    location = _clean(event.get("location") or DEFAULT_LOCATION)
    year = _clean(event.get("year") or "historical period")
    opponent = _clean(event.get("opponent") or "")
    evidence = build_slot_context(event, slot_key)
    section = _section_prompt(event, slot_key, slot_label)
    tension = f"Strategic tension/opposing force: {opponent}. " if opponent else ""
    prompt = (
        f"{BASE_STYLE_PROMPT}. Event: {title}. Year/time: {year}. Location: {location}. "
        f"Section/asset: {slot_key} - {slot_label}. Historical summary: {summary}. "
        f"{tension}{section} "
        "The image must read this exact section context, not a generic historical background. "
        f"Concrete event evidence to depict: {_clean(evidence, 720)}. "
        f"{TEXT_RULE} {AVOID_RULE}"
    )
    moderation = moderate_prompt(prompt)
    if moderation:
        raise ValueError(moderation)
    return prompt

def _section_prompt(event: dict[str, Any], slot_key: str, slot_label: str) -> str:
    if slot_key == "hero":
        return "Hero cover: a wide cinematic cover image and overview of the whole event, showing place, time, conflict, and result through landscape, forces, banners, weather, and symbolic action; no close-up faces."
    if slot_key == "context":
        return "Bối cảnh section: show the tense situation before the main event, preparations, scouts, terrain, political or military pressure, and quiet historical buildup; not the final battle climax."
    if slot_key.startswith("character-") or slot_key in {"leader", "founder", "key-figure"}:
        return _character_prompt(event, slot_key, slot_label)
    if slot_key.startswith("timeline-scene-"):
        index = _slot_index(slot_key)
        item = _timeline_item(event, index)
        return f"Diễn biến milestone: timeline scene {index}, show one specific chronological moment only. Milestone title: {_clean(item.get('title') or slot_label)}. Description/time: {_clean(_join_fields(item, ('day', 'month', 'year', 'date', 'description', 'mood')), 420)}. Use a distinct camera angle, lighting, action, terrain, and composition from other milestones."
    if slot_key.startswith("climax-phase-"):
        index = _slot_index(slot_key)
        phase = _climax_phase(event, _slot_index(slot_key))
        return f"Cao trào phase: climax phase panel {index}, depict the decisive turning point with strong tension, smoke/firelight/waves or equivalent event-specific pressure. Phase: {_clean(phase.get('label') or slot_label)}. Details: {_clean(_join_fields(phase, ('summary', 'description', 'keyDetail')), 460)}. Use action and environment, not a posed portrait."
    if slot_key == "climax":
        return "Cao trào section background: wide atmospheric background with powerful decisive-moment atmosphere, tactical pressure, smoke, firelight, banners, water or battlefield motion where relevant; cinematic but non-graphic, no detailed faces."
    if slot_key == "air-raid-map":
        return "Bản đồ chiến thuật: top-down air-defense operations map, ancient tactical parchment map style blended with radar arcs, aircraft approach paths, missile defense zones, route arrows, city silhouettes, abstract unit markers; no people, no faces, no modern map UI, avoid in-image labels."
    if slot_key == "battle-map":
        return "Bản đồ chiến thuật: top-down cartographic battle map, ancient tactical parchment map style, routes, arrows, terrain, rivers/roads/defense zones, ambush positions, fleet movement arrows, abstract unit markers; no people, no faces, no modern map UI, avoid in-image labels."
    if slot_key == "aftermath":
        return "Hệ quả section: quiet aftermath scene showing historical legacy, calmer symbolic scene after the event, changed landscape, banners, preserved traces, artifacts, dawn light, and long-term meaning; not active combat."
    if slot_key == "takeaway" or slot_key == "legacy":
        return "Bài học/di sản section: symbolic legacy scene with artifacts, monument, river/citadel/landscape memory, parchment tones, and reflective historical meaning; no people or only tiny indistinct figures."
    if slot_key == "capital":
        return "Place-focused section: architectural establishing view of Vietnamese historical terrain, architecture, settlement, river, citadel, road, fields, or strategic location; no central face."
    if slot_key == "key-place":
        return "Place-focused establishing view of Vietnamese historical terrain, architecture, settlement, river, citadel, road, fields, or strategic location; no central face."
    if slot_key == "setting":
        return "Environmental setting view of Vietnamese historical terrain, architecture, settlement, river, citadel, road, fields, or strategic location; no central face."
    if slot_key == "artifact":
        return "Museum object study: show artifact material texture, tools, evidence, display-like composition, and period context; no people, no faces."
    if slot_key in {"radar-command", "missile-site"}:
        return "Object/place-focused section: show tools, equipment, artifacts, command environment, or site layout as historical evidence; no people, no faces."
    if slot_key == "battlefield":
        return "Wide battlefield environment scene focused on terrain, formations, flags, smoke, weather, and strategic tension rather than individual combat detail."
    if slot_key == "practice":
        return "Cultural practice scene showing activity, tools, gestures, clothing silhouettes, and shared historical space; action matters more than any single face."
    if slot_key == "gathering":
        return "Wide public gathering scene showing assembly, banners or symbolic objects, shared purpose, and surrounding historical space; no close-up faces."
    if slot_key == "turning-point":
        return "Symbolic turning-point scene showing a decision, crossing, council, opened gate, changed route, or before-after tension that shows history changing direction."
    if slot_key == "reform":
        return "Reform and governance scene showing administrative change through court setting, documents as unreadable shapes, officials as distant figures, land or city planning."
    return f"Supporting section: create a contextual historical scene for {slot_label}, using section-specific action, terrain, props, colors, and educational clarity; no generic portrait."

def _character_prompt(event: dict[str, Any], slot_key: str, slot_label: str) -> str:
    character = _character_item(event, _slot_index(slot_key)) if slot_key.startswith("character-") else {}
    name = _clean(character.get("name") or slot_label)
    role = _clean(character.get("role") or "historical figure")
    side = _clean(character.get("side") or character.get("faction") or "")
    contribution = _clean(character.get("contribution") or character.get("bio") or character.get("description") or character.get("quote"), 360)
    palette = _palette_for(side, role, name)
    silhouette = _silhouette_for(role, side, name)
    setting = _setting_for(event, role, side)
    posture = _posture_for(role, side)
    return (
        f"Nhân vật chính: a stylized symbolic depiction representing {name}, not a real-person likeness. "
        f"Role differentiation: {role}. Faction/side: {side or 'historical side inferred from context'}. "
        f"Silhouette/costume: {silhouette}. Posture: {posture}. Personal setting/props: {setting}. "
        f"Color palette: {palette}. Contribution to show visually: {contribution}. "
        "Face not detailed, helmet shadow or three-quarter back view, no close-up realistic face, no photorealistic portrait."
    )

def _fallback_request(event: dict[str, Any], slot: dict[str, Any], level: int) -> dict[str, Any]:
    slot_key = str(slot.get("slot_key") or "hero")
    title = _clean(event.get("title") or "Sự kiện lịch sử Việt Nam")
    evidence = _clean(build_slot_context(event, slot_key), 520)
    if level == 1:
        prompt = (
            f"Safe retry level 1 for {title}, {slot_key}. {BASE_STYLE_PROMPT}. "
            "Use symbolic historical figures only, seen from behind or three-quarter back view, faces obscured by helmet shadow, small human figures, no detailed faces, no real-person likeness. "
            f"Depict the section evidence: {evidence}. {TEXT_RULE} {AVOID_RULE}"
        )
        return _request(prompt, _people_profile(), fallback_level=1)
    if level == 2:
        prompt = (
            f"Safe retry level 2 for {title}, {slot_key}. {BASE_STYLE_PROMPT}. "
            "No people, no faces. Use only contextual props and environment: tactical table, banners, boats, stakes, armor, helmet, sword, artifacts, river/citadel/terrain, smoke, light, and map elements. "
            f"Depict the section evidence: {evidence}. {TEXT_RULE} {AVOID_RULE}"
        )
        return _request(prompt, _no_people_profile(), fallback_level=2)
    prompt = (
        f"Safe retry level 3 for {title}, {slot_key}. Symbolic Vietnamese historical scene using only landscape, ships, banners, stakes, maps, artifacts, smoke, water, architecture, and light. "
        f"No people, no faces, no portraits. {BASE_STYLE_PROMPT}. Depict the section evidence: {evidence}. {TEXT_RULE} {AVOID_RULE}"
    )
    return _request(prompt, _no_people_profile(), fallback_level=3)

def _request(prompt: str, profile: dict[str, Any], fallback_level: int = 0) -> dict[str, Any]:
    moderation = moderate_prompt(prompt)
    if moderation:
        raise ValueError(moderation)
    return {
        "prompt": prompt,
        "negative_prompt": _join_negative_prompt(profile["negative_prompt"]),
        "person_generation": profile["person_generation"],
        "enhance_prompt": profile["enhance_prompt"],
        "aspect_ratio": "16:9",
        "fallback_level": fallback_level,
    }

def _profile_for_slot(slot_key: str) -> dict[str, Any]:
    if slot_key in {"battle-map", "air-raid-map", "capital", "key-place", "setting", "artifact", "radar-command", "missile-site", "takeaway", "legacy"}:
        return _no_people_profile()
    return _people_profile()

def _people_profile() -> dict[str, Any]:
    return {"person_generation": "ALLOW_ADULT", "enhance_prompt": False, "negative_prompt": "close-up portrait, close-up face, detailed face, realistic portrait, real-person likeness, modern people"}

def _no_people_profile() -> dict[str, Any]:
    return {"person_generation": "DONT_ALLOW", "enhance_prompt": False, "negative_prompt": "people, portraits, faces, hands, human figures, close-up characters"}

def _join_negative_prompt(slot_negative: str) -> str:
    return f"{BASE_NEGATIVE_PROMPT}, {slot_negative}"

def _event_data(event: dict[str, Any]) -> dict[str, Any]:
    story_json = event.get("story_json")
    if isinstance(story_json, dict):
        event_data = story_json.get("eventData")
        return event_data if isinstance(event_data, dict) else story_json
    return event

def _interactive(event: dict[str, Any]) -> dict[str, Any]:
    data = _event_data(event)
    return (event.get("interactive_data") if isinstance(event.get("interactive_data"), dict) else None) or data

def _timeline_item(event: dict[str, Any], index: int) -> dict[str, Any]:
    return _indexed_item(_interactive(event).get("timeline"), index) or {}

def _character_item(event: dict[str, Any], index: int) -> dict[str, Any]:
    return _indexed_item(_interactive(event).get("characters"), index) or {}

def _climax_phase(event: dict[str, Any], index: int) -> dict[str, Any]:
    scene = _interactive(event).get("climaxScene") or {}
    if not isinstance(scene, dict):
        return {}
    return _indexed_item(scene.get("phases"), index) or scene

def _palette_for(*values: str) -> str:
    text = " ".join(values).lower()
    if any(key in text for key in ("nguyên", "mông", "yuan", "pháp", "mỹ", "enemy", "opponent", "đối phương")):
        return "cold gray, dark blue, iron tones, harsher contrast"
    if any(key in text for key in ("đại việt", "việt", "quân ta", "ally", "commander", "tướng")):
        return "warm gold, deep red, earthy brown, bronze highlights"
    return "sepia, muted gold, parchment brown, restrained historical colors"

def _silhouette_for(role: str, side: str, name: str) -> str:
    text = f"{role} {side} {name}".lower()
    if any(key in text for key in ("king", "vua", "hoàng", "emperor")):
        return "royal battle robe, formal cloak, ceremonial headwear, upright ruler silhouette"
    if any(key in text for key in ("naval", "thủy", "fleet", "hạm", "ô mã")):
        return "naval armor, heavier shoulder silhouette, iron helmet, deck cloak"
    if any(key in text for key in ("scholar", "advisor", "mưu", "strategist")):
        return "scholar-strategist robe mixed with light armor, scroll/map props"
    if any(key in text for key in ("scout", "trinh sát")):
        return "light cloak, low profile stance, riverbank scouting gear"
    return "commander cloak, period armor, helmet shadow, banner-backed silhouette"

def _setting_for(event: dict[str, Any], role: str, side: str) -> str:
    location = _clean(event.get("location") or DEFAULT_LOCATION)
    text = f"{event.get('title', '')} {role} {side}".lower()
    if any(key in text for key in ("bạch đằng", "river", "sông", "naval", "thủy")):
        return f"riverbank or warship deck near {location}, wooden stakes, naval banners, tactical river map"
    if any(key in text for key in ("court", "vua", "hoàng", "political")):
        return f"Vietnamese court or citadel space at {location}, banners, scrolls, ceremonial architecture"
    return f"historical setting at {location}, tactical map, banners, terrain and section-specific props"

def _posture_for(role: str, side: str) -> str:
    text = f"{role} {side}".lower()
    if any(key in text for key in ("nguyên", "mông", "yuan", "đối phương", "opponent")):
        return "tense command stance, angled away from camera, surrounded by colder battle atmosphere"
    if any(key in text for key in ("strategist", "mưu", "advisor")):
        return "calm strategic stance, hand near map or command token, face partly hidden"
    return "authoritative heroic stance, three-quarter back view, face under helmet shadow"

def _slot_index(slot_key: str) -> int:
    try:
        return max(1, int(slot_key.rsplit("-", 1)[-1]))
    except ValueError:
        return 1

def _indexed_item(items: Any, index: int) -> dict[str, Any] | None:
    if not isinstance(items, list):
        return None
    zero_index = index - 1
    return items[zero_index] if 0 <= zero_index < len(items) and isinstance(items[zero_index], dict) else None

def _join_fields(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    return " ".join(str(item.get(key) or "") for key in keys)

def _clean(value: Any, limit: int | None = None) -> str:
    text_value = " ".join(str(value or "").split())
    if limit and len(text_value) > limit:
        return f"{text_value[:limit].rstrip()}..."
    return text_value
