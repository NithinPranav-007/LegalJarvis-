"""Structured judgment summarizer with per-sentence paragraph verification (Task T-16 / FR-09)."""

import logging
import re
from collections.abc import Sequence
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document
from app.llm.gateway import LLMGateway
from app.summarize.schemas import StructuredSummary, SummarySentence
from app.verify.support import compute_claim_passage_overlap

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE_PATH = Path("prompts/summary_v1.txt")


class StructuredSummarizer:
    """Summarizes Indian judgments into 5 rhetorical sections with per-sentence paragraph anchors."""

    def __init__(self, llm_gateway: LLMGateway | None = None) -> None:
        self.llm = llm_gateway or LLMGateway()

    def summarize_document(
        self,
        db: Session,
        document_id: int,
        max_sentences_per_section: int = 5,
    ) -> StructuredSummary:
        """Generate structured summary for a document with per-sentence paragraph anchors."""
        doc = db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document #{document_id} not found in database.")

        # Fetch chunks
        chunks = (
            db.execute(
                select(Chunk)
                .where(Chunk.document_id == document_id)
                .order_by(Chunk.para_no.asc().nulls_last(), Chunk.start_char.asc())
            )
            .scalars()
            .all()
        )

        case_title = doc.title or f"Judgment #{document_id}"

        if not chunks:
            return StructuredSummary(
                document_id=document_id,
                case_title=case_title,
                facts=[SummarySentence(text="No judgment text or paragraph chunks available.", source_para_nos=[])],
                overall_faithfulness_score=1.0,
            )

        # Build chunk paragraph lookup
        para_text_map: dict[int, str] = {}
        for c in chunks:
            if c.para_no:
                para_text_map[c.para_no] = c.text

        # Group chunks by rhetorical role
        by_role: dict[str, list[Chunk]] = {
            "facts": [],
            "issues": [],
            "arguments": [],
            "reasoning": [],
            "holding": [],
        }

        for c in chunks:
            role = (c.segment_type or "other").lower()
            if role in by_role:
                by_role[role].append(c)
            else:
                by_role["reasoning"].append(c)

        # Attempt generative summary if provider is active
        summary_raw: str | None = None
        if self.llm.is_available:
            try:
                summary_raw = self._generate_summary_llm(chunks)
            except Exception as e:
                logger.warning("LLM summarization call failed (%s), falling back to extractive: %s", type(e).__name__, e)

        # Parse LLM response or use extractive fallback
        if summary_raw:
            parsed = self._parse_summary_text(summary_raw)
        else:
            parsed = self._extractive_summary(by_role, max_sentences_per_section)

        # Verify paragraph support for every sentence
        verified_sections: dict[str, list[SummarySentence]] = {}
        total_sentences = 0
        supported_sentences = 0

        for section_name, raw_sentences in parsed.items():
            verified_list: list[SummarySentence] = []
            for s_text, para_nos in raw_sentences:
                total_sentences += 1
                if not para_nos:
                    # Sentence without paragraph citation is flagged unverified
                    verified_list.append(
                        SummarySentence(
                            text=s_text,
                            source_para_nos=[],
                            supported=False,
                            support_score=0.0,
                        )
                    )
                else:
                    # Check verification against all cited paragraphs
                    scores = []
                    for p in para_nos:
                        p_text = para_text_map.get(p, "")
                        score = compute_claim_passage_overlap(s_text, p_text)
                        scores.append(score)

                    avg_score = sum(scores) / len(scores) if scores else 0.0
                    is_supported = avg_score >= 0.20

                    if is_supported:
                        supported_sentences += 1

                    verified_list.append(
                        SummarySentence(
                            text=s_text,
                            source_para_nos=para_nos,
                            supported=is_supported,
                            support_score=round(avg_score, 3),
                        )
                    )
            verified_sections[section_name] = verified_list

        overall_score = (
            round(supported_sentences / total_sentences, 3) if total_sentences > 0 else 1.0
        )

        return StructuredSummary(
            document_id=document_id,
            case_title=case_title,
            facts=verified_sections.get("facts", []),
            issues=verified_sections.get("issues", []),
            arguments=verified_sections.get("arguments", []),
            reasoning=verified_sections.get("reasoning", []),
            holding=verified_sections.get("holding", []),
            overall_faithfulness_score=overall_score,
            total_sentences=total_sentences,
            supported_sentences=supported_sentences,
            unsupported_sentences=total_sentences - supported_sentences,
        )

    def _generate_summary_llm(self, chunks: Sequence[Chunk]) -> str:
        """Call LLM generator with prompt template."""
        # Format text with paragraph markers
        prompt_template = ""
        if PROMPT_TEMPLATE_PATH.is_file():
            prompt_template = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
        else:
            prompt_template = "Summarize the following judgment with [P<no>] citations:\n{text}"

        context_lines = []
        for c in chunks[:40]:  # Token-budgeted window
            p_marker = f"[P{c.para_no}]" if c.para_no else "[P0]"
            context_lines.append(f"{p_marker} {c.text}")

        full_prompt = prompt_template.format(text="\n\n".join(context_lines))
        response = self.llm.generate(prompt=full_prompt, max_tokens=1200, temperature=0.1)
        return response.content

    def _parse_summary_text(
        self,
        text: str,
    ) -> dict[str, list[tuple[str, list[int]]]]:
        """Parse structured LLM summary text into sections with extracted paragraph numbers."""
        sections: dict[str, list[tuple[str, list[int]]]] = {
            "facts": [],
            "issues": [],
            "arguments": [],
            "reasoning": [],
            "holding": [],
        }

        current_section = "facts"
        lines = text.split("\n")

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Detect section header
            upper = line_str.upper()
            if "FACTS" in upper:
                current_section = "facts"
                continue
            elif "ISSUE" in upper:
                current_section = "issues"
                continue
            elif "ARGUMENT" in upper:
                current_section = "arguments"
                continue
            elif "REASONING" in upper:
                current_section = "reasoning"
                continue
            elif "HOLDING" in upper:
                current_section = "holding"
                continue

            # Extract [P1], [P2] markers
            paras = [int(m) for m in re.findall(r"\[P(\d+)\]", line_str)]
            clean_text = re.sub(r"\[P\d+\]", "", line_str).strip()
            clean_text = re.sub(r"^\d+\.\s*", "", clean_text).strip()
            clean_text = re.sub(r"^[-*•]\s*", "", clean_text).strip()

            if clean_text:
                sections[current_section].append((clean_text, paras))

        return sections

    def _extractive_summary(
        self,
        by_role: dict[str, list[Chunk]],
        max_sentences: int,
    ) -> dict[str, list[tuple[str, list[int]]]]:
        """High-precision extractive fallback preserving exact paragraph citations."""
        res: dict[str, list[tuple[str, list[int]]]] = {
            "facts": [],
            "issues": [],
            "arguments": [],
            "reasoning": [],
            "holding": [],
        }

        for role, chunk_list in by_role.items():
            for c in chunk_list[:max_sentences]:
                p_no = c.para_no or 1
                # Split chunk into sentences
                sentences = re.split(r"(?<=[.!?])\s+", c.text.strip())
                for s in sentences:
                    s_clean = s.strip()
                    if len(s_clean) > 20:
                        res[role].append((s_clean, [p_no]))
                        if len(res[role]) >= max_sentences:
                            break
                if len(res[role]) >= max_sentences:
                    break

        return res
