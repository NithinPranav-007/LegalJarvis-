"""Unit and property tests for paragraph detection and offsets invariant (Task T-06 / FR-03)."""

from app.ingest.segment import (
    classify_segment,
    detect_paragraphs,
    segment_document,
)


def test_paragraph_number_detection() -> None:
    text = (
        "1. This is the first paragraph setting out the background.\n\n"
        "2. The High Court by the impugned judgment dismissed the writ petition.\n\n"
        "[3] Learned senior counsel appearing on behalf of the appellant contended that the order is perverse.\n\n"
        "(4) Having heard the rival submissions, we are of the considered opinion that the appeal deserves to succeed."
    )
    paras = detect_paragraphs(text)
    assert len(paras) == 4
    assert paras[0][0] == 1
    assert paras[1][0] == 2
    assert paras[2][0] == 3
    assert paras[3][0] == 4

    # Check text offsets roundtrip
    for _para_no, start, end, chunk_text in paras:
        assert end > start
        assert text[start:end] == chunk_text


def test_offsets_invariant_property() -> None:
    """Property test verifying text[start:end] == chunk.text for 100% of generated chunks."""
    sample_texts = [
        (
            "1. First paragraph of legal facts.\n\n"
            "2. Second paragraph with statutory analysis under Section 302 of the IPC.\n\n"
            "3. Third paragraph stating the final order and decree."
        ),
        (
            "FACTUAL BACKGROUND\n\n"
            "1. The appellant entered into an agreement to sell.\n\n"
            "ISSUES FRAMED\n\n"
            "2. Whether time was of the essence of the contract?\n\n"
            "REASONING AND CONCLUSION\n\n"
            "3. We find that the conduct of the parties clearly indicates waiver."
        ),
        (
            "No numbered paragraphs here.\n\n"
            "Just standard double newlines separating different paragraphs of text.\n\n"
            "And another concluding sentence."
        ),
    ]

    for raw in sample_texts:
        chunks = segment_document(raw)
        assert len(chunks) > 0
        for chunk in chunks:
            # Enforce 100% offset round-trip invariant
            assert chunk.end_char > chunk.start_char
            assert raw[chunk.start_char : chunk.end_char] == chunk.text
            assert chunk.segment_type in [
                "facts",
                "issues",
                "arguments",
                "reasoning",
                "holding",
                "other",
            ]


def test_segment_classification_keywords() -> None:
    assert classify_segment("BRIEF FACTS OF THE CASE") == "facts"
    assert classify_segment("ISSUES FOR CONSIDERATION") == "issues"
    assert classify_segment("SUBMISSIONS OF LEARNED COUNSEL") == "arguments"
    assert classify_segment("ANALYSIS AND REASONING") == "reasoning"
    assert classify_segment("OPERATIVE ORDER AND CONCLUSION") == "holding"
    assert classify_segment("MISCELLANEOUS SECTION") == "other"
