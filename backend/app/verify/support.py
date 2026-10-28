"""Per-sentence claim extraction and citation support verification (Task T-12 / FR-06)."""

import re
from dataclasses import dataclass, field

RE_CITATION_MARKER = re.compile(r"\[C(\d+)\]")

LEGAL_ABBREVS = {
    "v",
    "vs",
    "ltd",
    "pvt",
    "co",
    "corp",
    "inc",
    "sec",
    "art",
    "no",
    "ors",
    "anr",
    "dr",
    "mr",
    "mrs",
    "ms",
    "hon",
    "para",
    "cl",
    "uoi",
    "i.e",
    "e.g",
}

STOP_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "then",
    "of",
    "to",
    "in",
    "for",
    "on",
    "by",
    "with",
    "at",
    "from",
    "as",
    "is",
    "was",
    "are",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "under",
    "which",
    "who",
    "whom",
    "whose",
}


@dataclass
class SentenceSupportResult:
    sentence: str
    cited_markers: list[str] = field(default_factory=list)
    overlap_score: float = 0.0
    is_supported: bool = True
    rationale: str = ""


def normalize_citations(text: str) -> str:
    """Normalize citation formatting across varied LLM output styles.

    Handles:
    - Multi-citations: [C1, C2] or [C1,C2] or [C1; C2] -> [C1] [C2]
    - Case variations: [c1] -> [C1]
    - Nested brackets: ([C1]) -> [C1]
    - Trailing punctuation before citation: '...claim. [C1]' -> '...claim [C1].'
    """
    if not text:
        return ""

    # 1. Expand multi-citations e.g. [C1, C2, C3] or [1, 2] -> [C1] [C2] [C3]
    def expand_multicite(m: re.Match) -> str:
        inner = m.group(1)
        nums = re.findall(r"\b[cC]?(\d+)\b", inner)
        if nums:
            return " " + " ".join(f"[C{n}]" for n in nums)
        return m.group(0)

    res = re.sub(r"\[([cC]?\d+(?:\s*[,;]\s*[cC]?\d+)+)\]", expand_multicite, text)

    # 2. Case normalization: [c1] -> [C1]
    res = re.sub(r"\[[cC](\d+)\]", r"[C\1]", res)

    # 3. Strip redundant parentheses around citation: ([C1]) -> [C1]
    res = re.sub(r"\(\s*(\[C\d+\])\s*\)", r"\1", res)

    # 4. Bind citation marker to preceding sentence if placed after sentence-ending period
    # e.g., 'right to privacy. [C1]' -> 'right to privacy [C1].'
    res = re.sub(r"([.!?])\s*(\[C\d+\](?:\s*\[C\d+\])*)", r" \2\1", res)

    # Clean up double spaces
    res = re.sub(r"[ \t]+", " ", res)
    return res.strip()


def split_sentences_with_citations(text: str) -> list[str]:
    """Split text into sentences while keeping inline citations intact and protecting legal abbreviations."""
    norm_text = normalize_citations(text)
    if not norm_text:
        return []

    # Protect legal abbreviations like 'Ltd.', 'v.', 'Sec.', 'Art.' from being split
    def protect_abbrev(m: re.Match) -> str:
        word = m.group(1)
        if word.lower() in LEGAL_ABBREVS:
            return f"{word}___DOT___"
        return m.group(0)

    protected = re.sub(r"\b([a-zA-Z]{1,7})\.", protect_abbrev, norm_text)
    raw_parts = re.split(r"(?<=[.!?])\s+", protected.strip())
    sentences: list[str] = []

    for p in raw_parts:
        restored = p.replace("___DOT___", ".").strip()
        # Filter out empty strings or fragments that are purely punctuation and brackets
        if restored and not re.fullmatch(r"^[\[\]\d\s.,;C]+$", restored):
            sentences.append(restored)

    return sentences


def extract_keywords(text: str) -> set[str]:
    """Extract lowercased content keywords, removing stop words and markers."""
    clean_text = RE_CITATION_MARKER.sub(" ", text)
    tokens = re.findall(r"\b[a-zA-Z]{3,}\b", clean_text.lower())
    return {t for t in tokens if t not in STOP_WORDS}


def compute_claim_passage_overlap(claim: str, passage: str) -> float:
    """Calculate directional token overlap: fraction of claim keywords present in passage."""
    claim_words = extract_keywords(claim)
    if not claim_words:
        # Non-factual sentence (e.g. "In conclusion,")
        return 1.0

    passage_words = extract_keywords(passage)
    intersection = claim_words.intersection(passage_words)
    return float(len(intersection) / len(claim_words))


def verify_sentence_support(
    sentence: str,
    cited_passages: list[str],
    overlap_threshold: float = 0.25,
) -> SentenceSupportResult:
    """Check whether a single sentence is supported by its cited passage(s)."""
    norm_sentence = normalize_citations(sentence)
    markers = [f"[C{m.group(1)}]" for m in RE_CITATION_MARKER.finditer(norm_sentence)]

    if not markers:
        # A claim without any citation in a legal RAG answer is unsupported by default
        return SentenceSupportResult(
            sentence=sentence,
            cited_markers=[],
            overlap_score=0.0,
            is_supported=False,
            rationale="No citation provided for legal claim.",
        )

    # Filter out empty or whitespace-only passage strings
    valid_passages = [p.strip() for p in cited_passages if p and p.strip()]
    if not valid_passages:
        return SentenceSupportResult(
            sentence=sentence,
            cited_markers=markers,
            overlap_score=0.0,
            is_supported=False,
            rationale="Cited passage text was empty or not found in context.",
        )

    # Compute overlap against all cited passages and take the maximum
    best_score = 0.0
    for passage in valid_passages:
        score = compute_claim_passage_overlap(sentence, passage)
        if score > best_score:
            best_score = score

    supported = best_score >= overlap_threshold
    rationale = (
        f"Claim keyword overlap {best_score:.2f} >= threshold {overlap_threshold:.2f}."
        if supported
        else f"Claim keyword overlap {best_score:.2f} < threshold {overlap_threshold:.2f} (unsupported claim)."
    )

    return SentenceSupportResult(
        sentence=sentence,
        cited_markers=markers,
        overlap_score=round(best_score, 4),
        is_supported=supported,
        rationale=rationale,
    )
