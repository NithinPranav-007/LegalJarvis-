"""Unit tests with seeded failures for Citation Verifier and Abstention (Task T-12 / FR-06)."""

from app.retrieval.lexical import SearchResultItem
from app.verify.abstain import verify_and_filter_answer
from app.verify.existence import verify_citation_existence
from app.verify.support import compute_claim_passage_overlap, verify_sentence_support


def make_dummy_item(chunk_id: int, marker: str, text: str) -> SearchResultItem:
    return SearchResultItem(
        chunk_id=chunk_id,
        document_id=10,
        title="Eldeco Housing and Industries Ltd v. Ashok Vidyarthi",
        court="Supreme Court of India",
        decision_date="2023-11-28",
        neutral_citation="2023 INSC 1043",
        para_no=14,
        segment_type="reasoning",
        snippet=text,
        score=1.0,
    )


def test_verify_existence_seeded_fabricated_marker() -> None:
    """Seed 1: Test detection of fabricated citation markers not in retrieved context."""
    allowed = {"[C1]", "[C2]"}

    # Text containing fabricated marker [C99]
    answer_with_fake = (
        "The suit was decreed in favor of the appellant [C1]. "
        "However, the registration fee was waived by the registrar [C99]."
    )

    check = verify_citation_existence(answer_with_fake, allowed)
    assert check.is_valid is False
    assert check.has_hallucinations is True
    assert check.valid_markers == ["[C1]"]
    assert check.invalid_markers == ["[C99]"]

    # End-to-end verifier should abstain on hallucinated marker
    citation_map = {"[C1]": make_dummy_item(1, "[C1]", "Suit for specific performance decreed.")}
    v_res = verify_and_filter_answer(answer_with_fake, citation_map)
    assert v_res.passed is False
    assert v_res.abstained is True
    assert "[C99]" in v_res.invalid_citations
    assert "hallucinated citations" in v_res.abstention_reason.lower()


def test_verify_support_seeded_unsupported_claim() -> None:
    """Seed 2: Test detection of completely unsupported claim citing a real passage."""
    passage = "A suit for specific performance requires the plaintiff to establish readiness and willingness under Section 16(c) of Specific Relief Act."
    fake_claim = "The Supreme Court declared all cryptocurrency transactions tax-free under Article 19 [C1]."

    overlap = compute_claim_passage_overlap(fake_claim, passage)
    assert overlap == 0.0  # Zero overlap on factual legal words

    res = verify_sentence_support(fake_claim, [passage], overlap_threshold=0.25)
    assert res.is_supported is False
    assert res.overlap_score == 0.0
    assert "unsupported claim" in res.rationale.lower()


def test_verify_mixed_claims_pruning() -> None:
    """Seed 3: Test that verifier strips unsupported claims while preserving verified claims."""
    passage = "A suit for specific performance requires the plaintiff to establish readiness and willingness under Section 16(c) of Specific Relief Act."
    citation_map = {"[C1]": make_dummy_item(1, "[C1]", passage)}

    # Sentence 1 is supported; Sentence 2 is completely unsupported
    mixed_answer = (
        "Under Section 16(c), the plaintiff must establish readiness and willingness [C1]. "
        "The penalty for late delivery was reduced to fifty percent by the magistrate [C1]."
    )

    v_res = verify_and_filter_answer(
        mixed_answer,
        citation_map,
        overlap_threshold=0.25,
        min_supported_fraction=0.50,  # 1 of 2 = 50%
    )

    assert v_res.passed is True
    assert v_res.abstained is False
    # Sentence 1 kept, Sentence 2 pruned
    assert "readiness and willingness" in v_res.verified_answer
    assert "penalty for late delivery" not in v_res.verified_answer
    assert len(v_res.sentences) == 2
    assert v_res.sentences[0].is_supported is True
    assert v_res.sentences[1].is_supported is False


def test_verify_low_support_fraction_abstention() -> None:
    """Seed 4: Test that low supported sentence fraction (< min_supported_fraction) triggers full abstention."""
    passage = "A suit for specific performance requires readiness and willingness [C1]."
    citation_map = {"[C1]": make_dummy_item(1, "[C1]", passage)}

    # 1 supported sentence, 2 unsupported sentences -> 1/3 = 33.3% < 60% threshold
    bad_answer = (
        "The plaintiff must show readiness and willingness [C1]. "
        "All stamp duty charges were waived for the respondent [C1]. "
        "The arbitrator granted compound interest at eighteen percent [C1]."
    )

    v_res = verify_and_filter_answer(
        bad_answer,
        citation_map,
        overlap_threshold=0.25,
        min_supported_fraction=0.60,
    )

    assert v_res.passed is False
    assert v_res.abstained is True
    assert v_res.supported_fraction < 0.60
    assert "Abstained" in v_res.verified_answer
    assert "supported claim fraction" in v_res.abstention_reason.lower()


def test_verify_clean_answer_passes() -> None:
    """Test that a fully grounded answer passes verification with 100% score."""
    passage = "A suit for specific performance requires the plaintiff to establish readiness and willingness under Section 16(c) of Specific Relief Act."
    citation_map = {"[C1]": make_dummy_item(1, "[C1]", passage)}

    clean_answer = (
        "A suit for specific performance requires establishing readiness and willingness under Section 16(c) [C1]."
    )

    v_res = verify_and_filter_answer(clean_answer, citation_map)
    assert v_res.passed is True
    assert v_res.abstained is False
    assert v_res.supported_fraction == 1.0
    assert v_res.verified_answer == clean_answer
