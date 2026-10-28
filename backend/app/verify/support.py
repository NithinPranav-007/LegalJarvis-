"""Per-sentence claim extraction and citation support verification (Task T-12 / FR-06)."""

import re
from dataclasses import dataclass, field

RE_CITATION_MARKER = re.compile(r"\[C(\d+)\]")

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "of", "to", "in", "for",
    "on", "by", "with", "at", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "this", "that",
    "these", "those", "it", "its", "under", "which", "who", "whom", "whose",
}


@dataclass
class SentenceSupportResult:
    sentence: str
    cited_markers: list[str] = field(default_factory=list)
    overlap_score: float = 0.0
    is_supported: bool = True
    rationale: str = ""


def split_sentences_with_citations(text: str) -> list[str]:
    """Split text into sentences while keeping inline citations intact."""
    # Split by period followed by space or newline, but not inside abbreviations
    raw_parts = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences: list[str] = []
    for p in raw_parts:
        clean = p.strip()
        if clean:
            sentences.append(clean)
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
        # Trivial or non-factual sentence (e.g. "In conclusion,")
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
    markers = [f"[C{m.group(1)}]" for m in RE_CITATION_MARKER.finditer(sentence)]

    if not markers:
        # A claim without any citation in a legal RAG answer is unsupported by default
        return SentenceSupportResult(
            sentence=sentence,
            cited_markers=[],
            overlap_score=0.0,
            is_supported=False,
            rationale="No citation provided for legal claim.",
        )

    if not cited_passages:
        return SentenceSupportResult(
            sentence=sentence,
            cited_markers=markers,
            overlap_score=0.0,
            is_supported=False,
            rationale="Cited passage text was empty or not found in context.",
        )

    # Compute overlap against all cited passages and take the maximum
    best_score = 0.0
    for passage in cited_passages:
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
