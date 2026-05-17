from typing import Any

UNSAFE_TERMS = {"nude", "porn", "sexual", "gore", "bloodbath"}


def build_prompt(event: dict[str, Any], slot: dict[str, Any]) -> str:
    title = event.get("title") or "Su kien lich su Viet Nam"
    summary = event.get("summary") or title
    location = event.get("location") or "Viet Nam"
    slot_label = slot.get("slot_label") or slot.get("slot_key")
    prompt = (
        f"Historical educational illustration for Vietnamese history. "
        f"Event: {title}. Context: {summary}. Location: {location}. "
        f"Asset slot: {slot_label}. Style: cinematic, respectful, non-graphic, "
        f"accurate period clothing, no modern objects, no text overlay."
    )
    moderation = moderate_prompt(prompt)
    if moderation:
        raise ValueError(moderation)
    return prompt


def moderate_prompt(prompt: str) -> str | None:
    lowered = prompt.lower()
    if any(term in lowered for term in UNSAFE_TERMS):
        return "Prompt contains unsafe image content"
    return None
