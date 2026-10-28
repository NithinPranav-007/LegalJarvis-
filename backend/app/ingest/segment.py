"""Structure-aware segmentation and paragraph-anchored chunking (Task T-06 / FR-03)."""

import re
from dataclasses import dataclass

# Regex patterns for Indian court numbered paragraphs:
# Matches: "1.", "12.", "[1]", "(1)", "Para 1.", "Paragraph 1:"
RE_PARA_NUM = re.compile(
    r"(?:^|\n\n+)(?:(?:Para(?:graph)?\.?\s*)?(?:\[\s*(\d+)\s*\]|\((\d+)\)|(\d+)\.))\s+",
    re.MULTILINE,
)

# Heading keywords for rhetorical segments
SEGMENT_KEYWORDS = {
    "facts": [
        "factual background",
        "brief facts",
        "facts of the case",
        "factual matrix",
        "material facts",
        "case of the prosecution",
        "case of the appellant",
    ],
    "issues": [
        "issue for consideration",
        "issues for consideration",
        "issues framed",
        "question for consideration",
        "questions for consideration",
        "point for determination",
        "points for determination",
        "questions of law",
        "points of law",
        "issue:",
        "issues:",
    ],
    "arguments": [
        "submissions of",
        "contentions of",
        "contended by",
        "argued by",
        "counsel for the appellant",
        "counsel for the respondent",
    ],
    "reasoning": [
        "analysis",
        "reasoning",
        "we have considered",
        "discussion",
        "in our considered opinion",
        "legal position",
        "statutory interpretation",
    ],
    "holding": [
        "conclusion",
        "operative part",
        "order",
        "appeal is allowed",
        "appeal is dismissed",
        "petition is dismissed",
        "decree accordingly",
    ],
}


@dataclass
class SegmentSpan:
    segment_type: str
    start_char: int
    end_char: int
    heading: str | None = None


@dataclass
class ChunkRecord:
    para_no: int | None
    segment_type: str | None
    start_char: int
    end_char: int
    text: str
    is_parent: bool = False
    parent_index: int | None = None


def classify_segment(heading_text: str) -> str:
    """Classify text heading into one of the rhetorical segment types."""
    lower = heading_text.lower()
    for seg_type, keywords in SEGMENT_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return seg_type
    return "other"


def detect_paragraphs(text: str) -> list[tuple[int | None, int, int, str]]:
    """Detect numbered paragraphs or natural paragraph blocks with exact offsets.

    Returns: list of (para_no, start_char, end_char, chunk_text).
    """
    if not text:
        return []

    spans: list[tuple[int | None, int, int, str]] = []
    matches = list(RE_PARA_NUM.finditer(text))

    if matches:
        for i, match in enumerate(matches):
            para_num_str = match.group(1) or match.group(2) or match.group(3)
            para_no = int(para_num_str) if para_num_str else None

            start_char = match.start()
            # If match started with newlines, strip them from start_char
            while start_char < match.end() and text[start_char] in "\r\n":
                start_char += 1

            if i + 1 < len(matches):
                end_char = matches[i + 1].start()
            else:
                end_char = len(text)

            # Strip trailing whitespace from end_char while maintaining exact slice
            while end_char > start_char and text[end_char - 1] in "\r\n\t ":
                end_char -= 1

            chunk_text = text[start_char:end_char]
            if len(chunk_text.strip()) > 20:
                spans.append((para_no, start_char, end_char, chunk_text))
    else:
        # Fallback to double newline split if no numbered paragraphs found
        current_pos = 0
        para_counter = 1
        blocks = text.split("\n\n")
        for b in blocks:
            b_stripped = b.strip()
            if not b_stripped:
                current_pos += len(b) + 2
                continue
            start_char = text.find(b_stripped, current_pos)
            if start_char == -1:
                start_char = current_pos
            end_char = start_char + len(b_stripped)
            spans.append((para_counter, start_char, end_char, text[start_char:end_char]))
            current_pos = end_char
            para_counter += 1

    return spans


def segment_document(
    text: str,
    target_tokens: int = 400,
) -> list[ChunkRecord]:
    """Segment a judgment into parent and child chunks with 100% offset fidelity.

    Invariant: text[chunk.start_char:chunk.end_char] == chunk.text
    """
    if not text:
        return []

    paragraphs = detect_paragraphs(text)
    chunks: list[ChunkRecord] = []

    current_segment_type = "facts"

    for para_no, start_char, end_char, para_text in paragraphs:
        # Check first line for segment classification
        first_line = para_text.split("\n", 1)[0]
        detected = classify_segment(first_line)
        if detected != "other":
            current_segment_type = detected

        # Verify offset invariant before creating chunk
        assert (
            text[start_char:end_char] == para_text
        ), f"Offset mismatch at para {para_no}: {repr(text[start_char:end_char])} != {repr(para_text)}"

        chunk = ChunkRecord(
            para_no=para_no,
            segment_type=current_segment_type,
            start_char=start_char,
            end_char=end_char,
            text=para_text,
            is_parent=False,
        )
        chunks.append(chunk)

    return chunks
