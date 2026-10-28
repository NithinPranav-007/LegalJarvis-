"""Text cleaning, Unicode normalization, dehyphenation, and quality scoring."""

import re
import unicodedata


# Regex patterns for cleaning legal judgment texts
RE_HYPHEN_NEWLINE = re.compile(r"(\b[a-zA-Z]{2,})-\s*\n\s*([a-zA-Z]{2,}\b)")
RE_MULTI_NEWLINE = re.compile(r"\n{3,}")
RE_MULTI_SPACE = re.compile(r"[ \t]{2,}")
RE_SCR_HEADER = re.compile(
    r"(?i)(?:\[\d{4}\]\s*\d+\s*s\.?c\.?r\.?|\bSUPREME\s+COURT\s+REPORTS?\b|\bSUPREME\s+COURT\s+OF\s+INDIA\b|\bDIGITAL\s+SCR\b)",
)
RE_PAGE_NUM_ONLY = re.compile(r"^\s*(?:\[\s*\d+\s*\]|\d+)\s*$")


def normalize_unicode(text: str) -> str:
    """Normalize Unicode characters (NFKC) and replace irregular quotation/dash glyphs."""
    text = unicodedata.normalize("NFKC", text)
    # Smart quotes and apostrophes
    text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    # Dashes
    text = text.replace("—", " - ").replace("–", " - ")
    # Non-breaking spaces and zero-width spaces
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    return text


def dehyphenate(text: str) -> str:
    """Rejoin words split across line breaks by hyphens (e.g. juris-\ndiction -> jurisdiction)."""
    return RE_HYPHEN_NEWLINE.sub(r"\1\2", text)


def clean_page_lines(lines: list[str]) -> list[str]:
    """Filter out boilerplate headers, footers, and standalone page numbers."""
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if RE_PAGE_NUM_ONLY.match(stripped):
            continue
        if RE_SCR_HEADER.search(stripped) and len(stripped) < 80:
            continue
        cleaned.append(stripped)
    return cleaned


def clean_judgment_text(raw_text: str) -> str:
    """Complete cleaning pipeline: normalize, de-hyphenate, clean headers, and format whitespace."""
    normalized = normalize_unicode(raw_text)
    dehyphenated = dehyphenate(normalized)

    lines = dehyphenated.split("\n")
    cleaned_lines = clean_page_lines(lines)

    result = "\n".join(cleaned_lines)
    result = RE_MULTI_NEWLINE.sub("\n\n", result)
    return result.strip()


def compute_extraction_quality(text: str) -> float:
    """Compute extraction quality score between 0.0 and 1.0.

    Evaluates:
    - Minimum length threshold
    - Printable alphabetic character ratio
    - Reasonable word length distribution
    """
    if not text or len(text.strip()) < 50:
        return 0.0

    total_chars = len(text)
    alpha_chars = sum(1 for c in text if c.isalpha())
    printable_chars = sum(1 for c in text if c.isprintable() or c in "\n\t")

    alpha_ratio = alpha_chars / total_chars
    printable_ratio = printable_chars / total_chars

    # Token sanity check
    words = text.split()
    if not words:
        return 0.0

    valid_words = sum(1 for w in words if any(c.isalpha() for c in w) and len(w) <= 35)
    valid_word_ratio = valid_words / len(words)

    # Weighted composite quality score
    score = (alpha_ratio * 0.4) + (printable_ratio * 0.3) + (valid_word_ratio * 0.3)
    return round(min(max(score, 0.0), 1.0), 3)


def is_english_text(text: str, threshold: float = 0.70) -> bool:
    """Determine whether text is primarily English (Latin alphabet)."""
    if not text:
        return False

    alpha_chars = [c for c in text if c.isalpha()]
    if not alpha_chars:
        return False

    latin_chars = sum(1 for c in alpha_chars if "LATIN" in unicodedata.name(c, ""))
    ratio = latin_chars / len(alpha_chars)
    return ratio >= threshold
