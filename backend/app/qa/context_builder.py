"""Context assembly and passage budgeting for LLM prompt generation (Task T-11 / FR-05)."""

from dataclasses import dataclass, field

from app.retrieval.lexical import SearchResultItem


@dataclass
class AssembledContext:
    formatted_text: str
    citation_map: dict[str, SearchResultItem] = field(default_factory=dict)
    total_chars: int = 0
    num_passages: int = 0


def build_qa_context(
    items: list[SearchResultItem],
    max_chars: int = 12000,
) -> AssembledContext:
    """Format top retrieved items into numbered passage markers [C1], [C2]... with token budgeting."""
    passages: list[str] = []
    citation_map: dict[str, SearchResultItem] = {}
    current_chars = 0

    for idx, item in enumerate(items, start=1):
        marker = f"[C{idx}]"
        para_info = f"Para {item.para_no}" if item.para_no else "Judgment Body"
        cit_info = item.neutral_citation or "Citation Pending"

        block = (
            f"{marker} Title: {item.title}\n"
            f"Court: {item.court} | Citation: {cit_info} | {para_info}\n"
            f"Passage: {item.snippet}\n"
        )

        if current_chars + len(block) > max_chars and passages:
            # Budget reached, stop adding further passages
            break

        passages.append(block)
        citation_map[marker] = item
        current_chars += len(block)

    formatted_text = "\n".join(passages)
    return AssembledContext(
        formatted_text=formatted_text,
        citation_map=citation_map,
        total_chars=current_chars,
        num_passages=len(passages),
    )
