"""
Vietnamese text normalization utility.

Normalizes text for accent-insensitive search:
  - Lowercase
  - Convert đ → d, Đ → d
  - NFD decompose → strip combining diacritics (U+0300–U+036F)
  - Collapse multiple whitespace → single space
  - Trim

Usage:
    from app.utils.text import normalize_vietnamese
    normalized = normalize_vietnamese("Lý Thường Kiệt")
    # → "ly thuong kiet"
"""
import re
import unicodedata


def normalize_vietnamese(text: str) -> str:
    """Normalize Vietnamese text for accent-insensitive search."""
    if not text:
        return ""
    # Replace đ/Đ before NFD decomposition (no decomposition for đ)
    text = text.replace("đ", "d").replace("Đ", "d")
    # Lowercase
    text = text.lower()
    # NFD decompose → Unicode combining marks appear as separate codepoints
    text = unicodedata.normalize("NFD", text)
    # Remove combining diacritical marks
    text = re.sub(r"[\u0300-\u036f]", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_search_text(*fields: str) -> str:
    """Combine multiple fields into a single normalized search text."""
    combined = " ".join(f for f in fields if f)
    return normalize_vietnamese(combined)
