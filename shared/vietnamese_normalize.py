"""Vietnamese text normalization for full-text search."""
import re
import unicodedata


def normalize_vi(text: str) -> str:
    """Convert Vietnamese with diacritics to ASCII for search indexing."""
    text = text.lower()
    nfd = unicodedata.normalize("NFD", text)
    ascii_text = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    ascii_text = ascii_text.replace("đ", "d").replace("Đ", "d")
    ascii_text = re.sub(r"[^\w\s]", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()
