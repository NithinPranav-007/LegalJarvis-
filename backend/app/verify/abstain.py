"""Verification policy orchestrator enforcing claim pruning, query relevance, and threshold abstention (Task T-12 / FR-06)."""

from dataclasses import dataclass, field
from typing import Any

from app.qa.query_analysis import QueryAnalysisResult
from app.retrieval.lexical import SearchResultItem
from app.verify.existence import verify_citation_existence
from app.verify.relevance import verify_query_relevance
from app.verify.support import (
    SentenceSupportResult,
    normalize_citations,
    split_sentences_with_citations,
    verify_sentence_support,
)


@dataclass
class VerificationResult:
    raw_answer: str
    verified_answer: str
    sentences: list[SentenceSupportResult] = field(default_factory=list)
    invalid_citations: list[str] = field(default_factory=list)
    irrelevant_citations: list[str] = field(default_factory=list)
    supported_fraction: float = 1.0
    abstained: bool = False
    abstention_reason: str | None = None
    passed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "abstained": self.abstained,
            "abstention_reason": self.abstention_reason,
            "supported_fraction": self.supported_fraction,
            "invalid_citations": self.invalid_citations,
            "irrelevant_citations": self.irrelevant_citations,
            "sentence_evaluations": [
                {
                    "sentence": s.sentence,
                    "cited_markers": s.cited_markers,
                    "overlap_score": s.overlap_score,
                    "is_supported": s.is_supported,
                    "rationale": s.rationale,
                }
                for s in self.sentences
            ],
        }


def verify_and_filter_answer(
    answer: str,
    citation_map: dict[str, SearchResultItem],
    overlap_threshold: float = 0.25,
    min_supported_fraction: float = 0.60,
    query: str | None = None,
    query_analysis: QueryAnalysisResult | None = None,
) -> VerificationResult:
    """Enforce citation existence, query relevance, claim verification, sentence pruning, and abstention."""
    clean_ans = normalize_citations(answer.strip()) if answer else ""
    if not clean_ans:
        return VerificationResult(
            raw_answer="",
            verified_answer="",
            abstained=True,
            abstention_reason="Empty answer provided.",
            passed=False,
        )

    # 1. Verify existence of all cited markers
    allowed_markers = set(citation_map.keys()) if citation_map else set()
    existence = verify_citation_existence(clean_ans, allowed_markers)

    # 2. Query Relevance Verification (Task T-12 / Point 5: Cited passages must be relevant to the user query)
    irrelevant_markers: set[str] = set()
    relevance_evals: dict[str, Any] = {}
    if query or query_analysis:
        relevance_result = verify_query_relevance(
            query=query or (query_analysis.clean_query if query_analysis else ""),
            citation_map=citation_map,
            analysis=query_analysis,
        )
        irrelevant_markers = set(relevance_result.irrelevant_markers)
        relevance_evals = relevance_result.citation_evaluations

    # 3. Split answer into individual sentences
    raw_sentences = split_sentences_with_citations(clean_ans)
    if not raw_sentences:
        return VerificationResult(
            raw_answer=clean_ans,
            verified_answer="",
            abstained=True,
            abstention_reason="No parseable sentences found.",
            passed=False,
        )

    # 4. Evaluate each sentence
    sentence_results: list[SentenceSupportResult] = []
    supported_sentences: list[str] = []

    for sentence in raw_sentences:
        # Check if sentence cites hallucinated markers
        sent_existence = verify_citation_existence(sentence, allowed_markers)
        if not sent_existence.is_valid:
            # Contains invalid citation marker -> Immediately mark unsupported
            res = SentenceSupportResult(
                sentence=sentence,
                cited_markers=sent_existence.invalid_markers,
                overlap_score=0.0,
                is_supported=False,
                rationale=f"Contains hallucinated citation marker(s): {sent_existence.invalid_markers}",
            )
            sentence_results.append(res)
            continue

        # Check if cited markers are irrelevant to query
        active_relevant_markers = [m for m in sent_existence.valid_markers if m not in irrelevant_markers]
        if not active_relevant_markers and sent_existence.valid_markers:
            # All cited markers for this sentence are irrelevant to the user query
            first_m = sent_existence.valid_markers[0]
            irrel_rationale = (
                relevance_evals[first_m].rationale
                if first_m in relevance_evals
                else "Cited authority is irrelevant to the query."
            )
            res = SentenceSupportResult(
                sentence=sentence,
                cited_markers=sent_existence.valid_markers,
                overlap_score=0.0,
                is_supported=False,
                rationale=f"Query relevance check failed: {irrel_rationale}",
            )
            sentence_results.append(res)
            continue

        # Look up text for valid & relevant markers
        cited_passages: list[str] = []
        for marker in active_relevant_markers:
            item = citation_map.get(marker) if citation_map else None
            if item:
                snippet = getattr(item, "snippet", "") or getattr(item, "text", "")
                title = getattr(item, "title", "")
                cited_passages.append(f"{title} {snippet}".strip())

        res = verify_sentence_support(
            sentence=sentence,
            cited_passages=cited_passages,
            overlap_threshold=overlap_threshold,
        )
        sentence_results.append(res)
        if res.is_supported:
            supported_sentences.append(sentence)

    # 5. Compute supported fraction
    total_count = len(sentence_results)
    supported_count = len(supported_sentences)
    supported_fraction = round(supported_count / total_count, 4) if total_count > 0 else 0.0

    # 6. Abstention policy
    has_hallucinations = not existence.is_valid
    has_irrelevant_citations = bool(irrelevant_markers and any(m in clean_ans for m in irrelevant_markers))
    failed_threshold = supported_fraction < min_supported_fraction

    if has_hallucinations or failed_threshold or supported_count == 0 or (has_irrelevant_citations and supported_count == 0):
        reason_parts = []
        if has_hallucinations:
            reason_parts.append(f"hallucinated citations {existence.invalid_markers}")
        if has_irrelevant_citations:
            irr_desc = [relevance_evals[m].rationale for m in irrelevant_markers if m in relevance_evals]
            reason_parts.append(f"irrelevant authorities cited: {'; '.join(irr_desc)}")
        if failed_threshold:
            reason_parts.append(
                f"supported claim fraction {supported_fraction:.2f} < threshold {min_supported_fraction:.2f}"
            )
        elif supported_count == 0:
            reason_parts.append("zero claims supported by cited authorities")

        abstention_reason = f"Verification failed: {', '.join(reason_parts)}."

        target_case_desc = ""
        if query_analysis and query_analysis.target_case_name:
            target_case_desc = f" for '{query_analysis.target_case_name}'"

        verified_answer = (
            f"Abstained: The generated answer failed citation verification{target_case_desc}. "
            "One or more factual claims lacked direct grounding in verified, relevant legal authorities."
        )

        return VerificationResult(
            raw_answer=clean_ans,
            verified_answer=verified_answer,
            sentences=sentence_results,
            invalid_citations=existence.invalid_markers,
            irrelevant_citations=list(irrelevant_markers),
            supported_fraction=supported_fraction,
            abstained=True,
            abstention_reason=abstention_reason,
            passed=False,
        )

    # 7. Success: prune unsupported sentences and keep verified claims
    verified_answer = " ".join(supported_sentences)
    return VerificationResult(
        raw_answer=clean_ans,
        verified_answer=verified_answer,
        sentences=sentence_results,
        invalid_citations=[],
        irrelevant_citations=list(irrelevant_markers),
        supported_fraction=supported_fraction,
        abstained=False,
        abstention_reason=None,
        passed=True,
    )
