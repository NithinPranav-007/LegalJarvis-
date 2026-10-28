"""Unit tests verifying citation support, normalization, and threshold abstention (PRD T-12 / FR-06)."""

import pytest

from app.retrieval.lexical import SearchResultItem
from app.verify.abstain import verify_and_filter_answer
from app.verify.existence import verify_citation_existence
from app.verify.support import (
    compute_claim_passage_overlap,
    normalize_citations,
    split_sentences_with_citations,
    verify_sentence_support,
)


def make_dummy_item(chunk_id: int, marker: str, title: str, snippet: str) -> SearchResultItem:
    return SearchResultItem(
        chunk_id=chunk_id,
        document_id=1,
        title=title,
        court="Supreme Court of India",
        decision_date="2017-08-24",
        neutral_citation="2017 INSC 609",
        para_no=chunk_id,
        segment_type="holding",
        snippet=snippet,
        score=0.9,
    )


class TestCitationNormalizationAndSplitting:
    def test_normalize_multi_citations(self) -> None:
        raw = "This proposition is supported by multiple authorities [C1, C2] and [C3; C4]."
        norm = normalize_citations(raw)
        assert "[C1] [C2]" in norm
        assert "[C3] [C4]" in norm

    def test_normalize_trailing_punctuation_and_case(self) -> None:
        raw = "Privacy is a fundamental right. [c1] State cannot infringe it. [C2]"
        norm = normalize_citations(raw)
        assert "right [C1]." in norm
        assert "infringe it [C2]." in norm

    def test_split_sentences_protects_legal_abbreviations(self) -> None:
        text = (
            "In Eldeco Housing Ltd. v. Ashok Vidyarthi, the Supreme Court held readiness is required under Section 16(c) [C1]. "
            "The plaintiff must show continuous readiness and willingness [C2]."
        )
        sents = split_sentences_with_citations(text)
        assert len(sents) == 2
        assert "Eldeco Housing Ltd. v. Ashok Vidyarthi" in sents[0]
        assert "[C1]" in sents[0]
        assert "[C2]" in sents[1]


class TestCitationVerificationAndAbstention:
    def test_valid_supported_answer_single_citation(self) -> None:
        passage = "Privacy is a constitutionally protected right emerging from the right to life and personal liberty guaranteed under Article 21."
        citation_map = {"[C1]": make_dummy_item(1, "[C1]", "Puttaswamy", passage)}
        answer = "The right to privacy is recognized as a fundamental right guaranteed under Article 21 [C1]."

        res = verify_and_filter_answer(answer, citation_map, overlap_threshold=0.25, min_supported_fraction=0.60)
        assert res.passed is True
        assert res.abstained is False
        assert res.supported_fraction >= 0.60
        assert len(res.sentences) == 1
        assert res.sentences[0].is_supported is True

    def test_valid_supported_answer_multi_citations(self) -> None:
        p1 = "Under Section 302 IPC, murder is punishable with death or imprisonment for life."
        p2 = "Intention and knowledge are essential ingredients of murder under the penal code."
        citation_map = {
            "[C1]": make_dummy_item(1, "[C1]", "Murder Authority 1", p1),
            "[C2]": make_dummy_item(2, "[C2]", "Murder Authority 2", p2),
        }
        answer = "Murder is punishable under Section 302 with life imprisonment [C1]. Intention and knowledge are essential ingredients [C2]."

        res = verify_and_filter_answer(answer, citation_map, overlap_threshold=0.25, min_supported_fraction=0.60)
        assert res.passed is True
        assert res.abstained is False
        assert res.supported_fraction == 1.0

    def test_unsupported_answer_fails_threshold(self) -> None:
        passage = "The Airports Authority Act governs user development fee levies."
        citation_map = {"[C1]": make_dummy_item(1, "[C1]", "Airport Tax", passage)}
        # Claim contains unrelated words that have no overlap with the passage
        answer = "Anticipatory bail must be granted in all copyright infringement proceedings [C1]."

        res = verify_and_filter_answer(answer, citation_map, overlap_threshold=0.25, min_supported_fraction=0.60)
        assert res.passed is False
        assert res.abstained is True
        assert "supported claim fraction" in res.abstention_reason
        assert res.supported_fraction < 0.60

    def test_empty_retrieval_result_abstains(self) -> None:
        citation_map: dict[str, SearchResultItem] = {}
        answer = "Privacy is a fundamental right [C1]."

        res = verify_and_filter_answer(answer, citation_map, min_supported_fraction=0.60)
        assert res.passed is False
        assert res.abstained is True
        assert res.invalid_citations == ["[C1]"]

    def test_malformed_and_hallucinated_citations(self) -> None:
        passage = "Arbitrary state action violates Article 14."
        citation_map = {"[C1]": make_dummy_item(1, "[C1]", "Equality Case", passage)}
        answer = "State action must not be arbitrary [C1]. Furthermore, maritime limits apply [C999]."

        res = verify_and_filter_answer(answer, citation_map, min_supported_fraction=0.60)
        assert res.passed is False
        assert res.abstained is True
        assert "[C999]" in res.invalid_citations
        assert "hallucinated citations" in res.abstention_reason

    def test_missing_source_records_handled_gracefully(self) -> None:
        # Marker [C1] is theoretically in allowed_markers, but citation_map has None or missing snippet
        empty_item = make_dummy_item(1, "[C1]", "Empty Case", "")
        citation_map = {"[C1]": empty_item}
        answer = "Factual legal proposition with missing snippet [C1]."

        res = verify_and_filter_answer(answer, citation_map, min_supported_fraction=0.60)
        # Should not throw exception, but sentence should be unsupported
        assert res.sentences[0].is_supported is False
        assert res.abstained is True

    def test_claim_pruning_above_sixty_percent_threshold(self) -> None:
        p1 = "Article 21 protects personal liberty and dignity of individuals."
        citation_map = {"[C1]": make_dummy_item(1, "[C1]", "Liberty Case", p1)}
        # Sentence 1 is supported (citing C1). Sentence 2 is ungrounded (no citation).
        # We add 2 supported sentences and 1 unsupported: 2/3 = 0.667 >= 0.60 threshold.
        answer = (
            "Article 21 protects personal liberty and dignity of individuals [C1]. "
            "Personal liberty is guaranteed to every individual under Article 21 [C1]. "
            "An invented claim about space law without citation."
        )

        res = verify_and_filter_answer(answer, citation_map, overlap_threshold=0.25, min_supported_fraction=0.60)
        assert res.passed is True
        assert res.abstained is False
        assert res.supported_fraction >= 0.60
        # The unsupported sentence must be pruned from verified_answer
        assert "space law" not in res.verified_answer
        assert "Article 21 protects personal liberty" in res.verified_answer
