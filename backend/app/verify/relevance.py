"""Query-relevance verification ensuring citations address requested cases, citations, and legal issues (Task T-12 / FR-06)."""

import re
from dataclasses import dataclass, field
from typing import Any

from app.qa.query_analysis import QueryAnalysisResult, analyze_query
from app.retrieval.lexical import SearchResultItem
from app.verify.support import STOP_WORDS

# Generic legal query stopwords that do not indicate substantive topical relevance
GENERIC_LEGAL_STOPWORDS = STOP_WORDS.union({
    "search",
    "find",
    "corpus",
    "indian",
    "supreme",
    "court",
    "high",
    "judgment",
    "judgments",
    "case",
    "cases",
    "order",
    "orders",
    "decision",
    "decisions",
    "ruling",
    "rulings",
    "explain",
    "explaining",
    "main",
    "legal",
    "issue",
    "issues",
    "reasoning",
    "reasons",
    "final",
    "using",
    "only",
    "retrieved",
    "passage",
    "passages",
    "holding",
    "ratio",
    "decidendi",
    "versus",
    "what",
    "which",
    "when",
    "where",
    "who",
    "whom",
    "whose",
    "why",
    "how",
    "para",
    "paragraph",
    "paragraphs",
    "state",
    "union",
    "india",
    "requirement",
    "requirements",
})


@dataclass
class CitationRelevanceResult:
    marker: str
    is_relevant: bool
    title: str
    rationale: str
    overlap_score: float = 0.0


@dataclass
class QueryRelevanceVerificationResult:
    is_fully_relevant: bool
    citation_evaluations: dict[str, CitationRelevanceResult] = field(default_factory=dict)
    irrelevant_markers: list[str] = field(default_factory=list)
    relevance_ratio: float = 1.0
    summary_rationale: str | None = None


def _extract_substantive_tokens(text: str) -> set[str]:
    """Extract lowercased substantive tokens excluding generic legal stopwords."""
    tokens = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return {t for t in tokens if t not in GENERIC_LEGAL_STOPWORDS}


def _case_name_matches(target_case: str, doc_title: str) -> tuple[bool, str]:
    """Check if document title matches requested case name."""
    t_case_clean = target_case.strip().lower()
    d_title_clean = doc_title.strip().lower()

    if t_case_clean in d_title_clean or d_title_clean in t_case_clean:
        return True, "Exact case name substring match."

    # Extract party tokens
    def get_parties(name: str) -> list[set[str]]:
        parts = re.split(r"\b(?:v\.|vs\.|versus|v)\b", name, flags=re.IGNORECASE)
        party_sets = []
        for p in parts:
            toks = {
                t
                for t in re.findall(r"\b[a-zA-Z]{3,}\b", p.lower())
                if t not in {"state", "union", "india", "ltd", "pvt", "ors", "anr"}
            }
            if toks:
                party_sets.append(toks)
        return party_sets

    target_parties = get_parties(target_case)
    doc_parties = get_parties(doc_title)

    if not target_parties or not doc_parties:
        # Fallback to token intersection
        target_tokens = _extract_substantive_tokens(target_case)
        doc_tokens = _extract_substantive_tokens(doc_title)
        inter = target_tokens.intersection(doc_tokens)
        if len(inter) >= max(2, int(len(target_tokens) * 0.5)):
            return True, f"Party token match: {inter}"
        return False, f"Case titles diverge: requested '{target_case}', got '{doc_title}'."

    # Primary party match (Party 1)
    p1_target = target_parties[0]
    p1_doc = doc_parties[0] if doc_parties else set()

    p1_inter = p1_target.intersection(p1_doc)
    # Check if primary distinctive party matches (e.g. 'Puttaswamy', 'Sarda', 'Bhajan', 'Eldeco')
    if len(p1_inter) >= 1 and any(len(t) > 3 for t in p1_inter):
        return True, f"Party 1 distinctive token match: {p1_inter}"

    return False, f"Requested case '{target_case}' does not match cited judgment '{doc_title}'."


def verify_query_relevance(
    query: str,
    citation_map: dict[str, SearchResultItem],
    analysis: QueryAnalysisResult | None = None,
) -> QueryRelevanceVerificationResult:
    """Verify that cited authorities and passages in citation_map are relevant to the query.

    Ensures that an unrelated judgment (e.g. Sharad Birdhichand Sarda) is not substituted
    when a specific case (e.g. All India Judges Association) was requested.
    """
    if not citation_map:
        return QueryRelevanceVerificationResult(
            is_fully_relevant=True,
            citation_evaluations={},
            irrelevant_markers=[],
            relevance_ratio=1.0,
            summary_rationale="No citations to verify.",
        )

    if analysis is None:
        analysis = analyze_query(query)

    query_substantive = _extract_substantive_tokens(query)
    evaluations: dict[str, CitationRelevanceResult] = {}
    irrelevant_markers: list[str] = []

    for marker, item in citation_map.items():
        title = getattr(item, "title", "") or ""
        snippet = getattr(item, "snippet", "") or getattr(item, "text", "") or ""
        neutral_cit = getattr(item, "neutral_citation", "") or ""
        decision_date = getattr(item, "decision_date", "") or ""

        # 1. Target Case Verification
        if analysis.target_case_name:
            matches, rationale = _case_name_matches(analysis.target_case_name, title)
            if not matches:
                # Target case specified, but cited document belongs to an entirely different case
                evaluations[marker] = CitationRelevanceResult(
                    marker=marker,
                    is_relevant=False,
                    title=title,
                    rationale=(
                        f"Cited authority '{title}' does not match requested case "
                        f"'{analysis.target_case_name}'."
                    ),
                    overlap_score=0.0,
                )
                irrelevant_markers.append(marker)
                continue

        # 2. Target Citation Verification
        if analysis.target_citations:
            cit_matched = any(
                tc.lower() in neutral_cit.lower() or tc.lower() in title.lower()
                for tc in analysis.target_citations
            )
            if not cit_matched and not analysis.target_case_name:
                evaluations[marker] = CitationRelevanceResult(
                    marker=marker,
                    is_relevant=False,
                    title=title,
                    rationale=(
                        f"Cited citation '{neutral_cit}' does not match requested citation(s) "
                        f"{analysis.target_citations}."
                    ),
                    overlap_score=0.0,
                )
                irrelevant_markers.append(marker)
                continue

        # 3. Target Year Verification (if requested year strongly mismatches cited judgment year)
        if analysis.target_year and decision_date:
            try:
                doc_year = int(decision_date[:4])
                # If target year was explicitly asked (e.g. 2023 judgment) and doc year differs by > 5 years,
                # and case name was not an exact match
                if abs(doc_year - analysis.target_year) > 2 and not analysis.target_case_name:
                    evaluations[marker] = CitationRelevanceResult(
                        marker=marker,
                        is_relevant=False,
                        title=title,
                        rationale=(
                            f"Cited judgment year {doc_year} does not match requested year "
                            f"{analysis.target_year}."
                        ),
                        overlap_score=0.0,
                    )
                    irrelevant_markers.append(marker)
                    continue
            except ValueError:
                pass

        # 4. Topical substantive overlap check (for conceptual / general queries)
        passage_substantive = _extract_substantive_tokens(f"{title} {snippet}")
        if query_substantive and not analysis.target_case_name and not analysis.target_citations:
            overlap = query_substantive.intersection(passage_substantive)
            overlap_frac = len(overlap) / len(query_substantive)
            # Require at least 1 substantive content keyword match or >= 10% overlap
            if len(overlap) == 0:
                evaluations[marker] = CitationRelevanceResult(
                    marker=marker,
                    is_relevant=False,
                    title=title,
                    rationale="Passage contains no substantive topical overlap with the question.",
                    overlap_score=round(overlap_frac, 4),
                )
                irrelevant_markers.append(marker)
                continue
            else:
                evaluations[marker] = CitationRelevanceResult(
                    marker=marker,
                    is_relevant=True,
                    title=title,
                    rationale=f"Passage matches topical keywords: {overlap}",
                    overlap_score=round(overlap_frac, 4),
                )
                continue

        # If it reached here, it passed relevant checks
        evaluations[marker] = CitationRelevanceResult(
            marker=marker,
            is_relevant=True,
            title=title,
            rationale="Authority and passage verified relevant to query.",
            overlap_score=1.0,
        )

    total_citations = len(citation_map)
    relevant_count = total_citations - len(irrelevant_markers)
    ratio = round(relevant_count / total_citations, 4) if total_citations > 0 else 1.0
    fully_relevant = len(irrelevant_markers) == 0

    summary = (
        "All citations verified relevant to query."
        if fully_relevant
        else f"{len(irrelevant_markers)} citation(s) failed query relevance check: {irrelevant_markers}"
    )

    return QueryRelevanceVerificationResult(
        is_fully_relevant=fully_relevant,
        citation_evaluations=evaluations,
        irrelevant_markers=irrelevant_markers,
        relevance_ratio=ratio,
        summary_rationale=summary,
    )
