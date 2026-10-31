"""QA Orchestrator assembling retrieval, prompts, generator, and citation resolution (Task T-11 / FR-05)."""

import logging
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import log_audit_event
from app.db.models import Document
from app.llm.gateway import LLMGateway, get_llm_gateway
from app.qa.context_builder import build_qa_context
from app.qa.guardrails import check_input_guardrails
from app.qa.query_analysis import QueryAnalysisResult, analyze_query
from app.retrieval.hybrid import search_hybrid
from app.schemas.qa import QACitation, QAResponse
from app.verify.abstain import verify_and_filter_answer

logger = logging.getLogger(__name__)

RE_CITATION_MARKER = re.compile(r"\[C(\d+)\]")
ABSTENTION_MARKER = "[INSUFFICIENT_EVIDENCE]"

# Default path to prompt template
DEFAULT_PROMPT_PATH = Path("prompts/qa_v1.txt")


def load_qa_prompt_template(path: Path | str | None = None) -> str:
    """Load the versioned QA prompt template from disk."""
    p = Path(path) if path else DEFAULT_PROMPT_PATH
    if not p.exists():
        # Fallback inline template if file cannot be read
        return (
            "You are Needhi, a citation-verified legal research assistant.\n"
            "Answer using ONLY the numbered passages below.\n"
            "Cite passages using [C1], [C2].\n"
            "If evidence is insufficient, output [INSUFFICIENT_EVIDENCE].\n\n"
            "CONTEXT PASSAGES:\n{context}\n\nQUESTION:\n{question}\n\nANSWER:\n"
        )
    return p.read_text(encoding="utf-8")


def get_matching_case_documents(db: Session, target_case_name: str) -> list[Document]:
    """Find documents matching the target case name in the corpus."""
    parts = re.split(r"\b(?:v\.|vs\.|versus|v)\b", target_case_name, flags=re.IGNORECASE)
    party1 = parts[0].strip() if parts else target_case_name.strip()
    p1_tokens = [
        t.lower()
        for t in re.findall(r"\b[a-zA-Z]{3,}\b", party1)
        if t.lower() not in {"the", "and", "for", "all", "india", "state", "union"}
    ]
    if not p1_tokens:
        p1_tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z]{3,}\b", party1)]

    docs = db.query(Document).all()
    matching: list[Document] = []
    for d in docs:
        if not d.title:
            continue
        t_low = d.title.lower()
        if target_case_name.lower() in t_low or t_low in target_case_name.lower():
            matching.append(d)
        elif p1_tokens and all(tok in t_low for tok in p1_tokens):
            matching.append(d)

    return matching


class QAOrchestrator:
    """Orchestrates query analysis, hybrid retrieval, prompt formatting, and LLM inference."""

    def __init__(
        self,
        gateway: LLMGateway | None = None,
        prompt_template: str | None = None,
    ):
        self._gateway = gateway or get_llm_gateway()
        self._prompt_template = prompt_template or load_qa_prompt_template()

    def ask(
        self,
        db: Session,
        question: str,
        court_codes: list[str] | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        limit: int = 6,
    ) -> QAResponse:
        """Execute full cited Question-Answering pipeline."""
        clean_q = question.strip()

        # 0. Safety & Legal-Advice Guardrails (FR-17)
        guardrail = check_input_guardrails(clean_q)
        if not guardrail.is_safe:
            return QAResponse(
                question=clean_q,
                answer=guardrail.refusal_message or "Request refused under safety guidelines.",
                citations=[],
                abstained=True,
                abstention_reason=guardrail.reason,
                disclaimer=settings.LEGAL_DISCLAIMER,
                generation_status="refused",
            )

        # 1. Query Analysis (detect sections, statutes, criminal transition notice, case names, years)
        analysis = analyze_query(clean_q)

        # 1b. Target Case Corpus Coverage Verification (Task T-11 / FR-05)
        # If the user specifically asks for a target case that is not in the corpus, abstain immediately.
        # Do NOT substitute unrelated precedents (Rule 2 & 3: Never fabricate or substitute cases).
        matching_docs: list[Document] = []
        if analysis.target_case_name:
            matching_docs = get_matching_case_documents(db, analysis.target_case_name)
            if not matching_docs:
                year_desc = f"{analysis.target_year} " if analysis.target_year else ""
                abstention_msg = (
                    f"The requested {year_desc}judgment in '{analysis.target_case_name}' is not present "
                    "in the indexed Supreme Court corpus. Needhi will not substitute unrelated precedents."
                )
                return QAResponse(
                    question=clean_q,
                    answer=abstention_msg,
                    citations=[],
                    abstained=True,
                    abstention_reason=f"Target case '{analysis.target_case_name}' not found in indexed corpus.",
                    criminal_transition_notice=analysis.notice_text,
                    disclaimer=settings.LEGAL_DISCLAIMER,
                    generation_status="abstained",
                )

        # 2. Hybrid Retrieval with reranking
        hits = search_hybrid(
            db=db,
            query=clean_q,
            court_codes=court_codes,
            year_from=year_from,
            year_to=year_to,
            limit=limit,
            rerank=True,
        )

        # If a specific target case was requested, filter hits strictly to the target case
        if matching_docs:
            matching_doc_ids = {d.id for d in matching_docs}
            case_hits = [h for h in hits if h.document_id in matching_doc_ids]
            if case_hits:
                hits = case_hits

        # 3. Empty corpus check -> Abstain
        if not hits:
            return QAResponse(
                question=clean_q,
                answer="No relevant judgments or statutory passages were found in the corpus to answer this question.",
                citations=[],
                abstained=True,
                abstention_reason="No relevant passages retrieved from corpus.",
                criminal_transition_notice=analysis.notice_text,
                disclaimer=settings.LEGAL_DISCLAIMER,
                generation_status="abstained",
            )

        # 4. Context Assembly & Passage Budgeting
        context = build_qa_context(hits)

        # 5. Check LLM provider availability (Graceful degradation per FR-05)
        if not self._gateway.has_credentials and self._gateway.provider_name != "fake":
            degraded_citations = [
                QACitation(
                    marker=marker,
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    title=item.title,
                    court=item.court,
                    neutral_citation=item.neutral_citation,
                    para_no=item.para_no,
                    snippet=item.snippet,
                    attribution=item.attribution,
                )
                for marker, item in context.citation_map.items()
            ]
            return QAResponse(
                question=clean_q,
                answer=(
                    "Automated synthesis is currently unavailable (no active LLM credentials configured). "
                    "The top authoritative passages retrieved from the legal corpus are listed below for reference."
                ),
                citations=degraded_citations,
                abstained=False,
                abstention_reason=None,
                criminal_transition_notice=analysis.notice_text,
                disclaimer=settings.LEGAL_DISCLAIMER,
                generation_status="generation_unavailable",
            )

        # 6. Prompt Formulation
        prompt = self._prompt_template.format(
            context=context.formatted_text,
            question=clean_q,
        )

        # 7. LLM Generation
        try:
            llm_resp = self._gateway.generate(
                prompt=prompt,
                system_prompt="You are Needhi, a citation-verified legal research assistant for Indian law.",
                temperature=0.0,
            )
            raw_answer = llm_resp.content.strip()
        except Exception as exc:
            logger.error("LLM generation failed: %s", exc)
            degraded_citations = [
                QACitation(
                    marker=marker,
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    title=item.title,
                    court=item.court,
                    neutral_citation=item.neutral_citation,
                    para_no=item.para_no,
                    snippet=item.snippet,
                    attribution=item.attribution,
                )
                for marker, item in context.citation_map.items()
            ]
            return QAResponse(
                question=clean_q,
                answer=(f"LLM generator error ({exc}). Returning retrieved source passages only."),
                citations=degraded_citations,
                abstained=False,
                abstention_reason=None,
                criminal_transition_notice=analysis.notice_text,
                disclaimer=settings.LEGAL_DISCLAIMER,
                generation_status="generation_unavailable",
            )

        # 8. Check for explicit abstention token
        if ABSTENTION_MARKER in raw_answer:
            explanation = raw_answer.replace(ABSTENTION_MARKER, "").strip()
            return QAResponse(
                question=clean_q,
                answer=explanation
                or "The available legal context does not contain sufficient evidence to answer this question.",
                citations=[],
                abstained=True,
                abstention_reason="Insufficient evidence in retrieved passages.",
                criminal_transition_notice=analysis.notice_text,
                disclaimer=settings.LEGAL_DISCLAIMER,
                generation_status="abstained",
            )

        # 9. Citation Verification & Query-Relevance Filtering (Task T-12 / FR-06)
        verification = verify_and_filter_answer(
            answer=raw_answer,
            citation_map=context.citation_map,
            overlap_threshold=0.25,
            min_supported_fraction=0.60,
            query=clean_q,
            query_analysis=analysis,
        )

        if verification.abstained:
            return QAResponse(
                question=clean_q,
                answer=verification.verified_answer,
                citations=[],
                abstained=True,
                abstention_reason=verification.abstention_reason,
                criminal_transition_notice=analysis.notice_text,
                disclaimer=settings.LEGAL_DISCLAIMER,
                generation_status="abstained",
            )

        final_answer = verification.verified_answer

        # 10. Citation Resolution
        cited_markers = set(f"[C{m.group(1)}]" for m in RE_CITATION_MARKER.finditer(final_answer))
        active_citations: list[QACitation] = []

        for marker, item in context.citation_map.items():
            if marker in cited_markers or not cited_markers:
                active_citations.append(
                    QACitation(
                        marker=marker,
                        chunk_id=item.chunk_id,
                        document_id=item.document_id,
                        title=item.title,
                        court=item.court,
                        neutral_citation=item.neutral_citation,
                        para_no=item.para_no,
                        snippet=item.snippet,
                        attribution=item.attribution,
                    )
                )

        # Audit logging (FR-18)
        log_audit_event(
            event_type="qa_query",
            query=clean_q,
            retrieval_chunk_ids=[c.chunk_id for c in active_citations],
            model_identifier=self._gateway.provider_name,
            verification_outcome="verified",
        )

        return QAResponse(
            question=clean_q,
            answer=final_answer,
            citations=active_citations,
            abstained=False,
            abstention_reason=None,
            criminal_transition_notice=analysis.notice_text,
            disclaimer=settings.LEGAL_DISCLAIMER,
            generation_status="completed",
        )
