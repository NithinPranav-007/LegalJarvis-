"""Gold standard dataset import, validation, and disjointness enforcement (Task T-18 / FR-16, Part G)."""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ALLOWED_SUBJECTS = {
    "criminal",
    "constitutional",
    "civil",
    "property",
    "service",
    "tax",
    "arbitration",
    "statutory",
}

ADVERSARIAL_CATEGORIES = {
    "false_premise",
    "repealed_provision",
    "non_existent_case",
    "out_of_corpus",
}


@dataclass
class GoldQAItem:
    id: str
    question: str
    reference_answer: str
    target_document_ids: list[int]
    gold_paragraph_nos: list[int]
    subject_area: str
    decision_year: int
    reviewer_initials: str
    is_adversarial: bool = False
    adversarial_category: str | None = None
    disallow_tuning: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_gold_qa_item(data: dict[str, Any]) -> tuple[bool, str | None]:
    """Validate a human-labelled gold QA record against strict PRD rules.

    Rules:
    1. Human Reviewer Initials required (Rule 1 & Rule 3: No auto-generated gold answers).
    2. Decision Year >= 2023 to avoid pre-2023 LLM pre-training contamination.
    3. Valid subject area or adversarial category.
    4. Exact source paragraph numbers required for non-adversarial questions.
    """
    item_id = data.get("id")
    if not item_id:
        return False, "Missing required field: 'id'"

    question = (data.get("question") or "").strip()
    if not question:
        return False, f"Item {item_id}: question text cannot be empty"

    ref_answer = (data.get("reference_answer") or "").strip()
    if not ref_answer:
        return False, f"Item {item_id}: reference_answer cannot be empty"

    reviewer = (data.get("reviewer_initials") or "").strip()
    if not reviewer:
        return False, (
            f"Item {item_id}: missing 'reviewer_initials'. "
            "Rule 1 & T-18: Gold answers must be produced by certified human legal reviewers, never auto-generated."
        )

    # Reject synthetic / automated labels posing as reviewers
    rev_lower = reviewer.lower()
    if any(bot in rev_lower for bot in ["ai", "gpt", "bot", "auto", "synthetic", "llm", "claude", "gemini"]):
        return False, f"Item {item_id}: Invalid reviewer '{reviewer}'. Automated reviewers are strictly prohibited."

    year = data.get("decision_year", 0)
    if year < 2023 and not data.get("is_adversarial"):
        return False, f"Item {item_id}: Decision year {year} < 2023. Gold sets must use 2023+ judgments to prevent pre-training contamination."

    subject = (data.get("subject_area") or "").lower()
    if subject not in ALLOWED_SUBJECTS and not data.get("is_adversarial"):
        return False, f"Item {item_id}: Invalid subject_area '{subject}'. Must be one of {sorted(ALLOWED_SUBJECTS)}"

    is_adversarial = bool(data.get("is_adversarial", False))
    if is_adversarial:
        adv_cat = data.get("adversarial_category")
        if adv_cat not in ADVERSARIAL_CATEGORIES:
            return False, f"Item {item_id}: Adversarial items must specify valid category in {sorted(ADVERSARIAL_CATEGORIES)}"
    else:
        doc_ids = data.get("target_document_ids", [])
        if not doc_ids:
            return False, f"Item {item_id}: Non-adversarial gold item must link to at least one target_document_id"
        paras = data.get("gold_paragraph_nos", [])
        if not paras:
            return False, f"Item {item_id}: Non-adversarial gold item must provide exact gold_paragraph_nos"

    return True, None


def verify_gold_tuning_disjointness(
    gold_items: list[dict[str, Any]],
    tuning_document_ids: set[int],
) -> tuple[bool, set[int]]:
    """Enforce strict disjointness between evaluation gold set and training/tuning corpus.

    Per PRD Section D8 / Part G:
    "No LJ-Gold item, and no document linked to one, may appear in any tuning set. A test asserts disjointness."
    """
    gold_doc_ids: set[int] = set()
    for item in gold_items:
        docs = item.get("target_document_ids", [])
        for d in docs:
            gold_doc_ids.add(int(d))

    overlap = gold_doc_ids.intersection(tuning_document_ids)
    if overlap:
        logger.error("Data leakage detected! %d documents appear in both gold set and tuning set: %s", len(overlap), overlap)
        return False, overlap

    logger.info("Disjointness check passed: 0 overlap between %d gold documents and %d tuning documents.", len(gold_doc_ids), len(tuning_document_ids))
    return True, set()


def load_gold_qa_file(path: Path) -> list[GoldQAItem]:
    """Load and validate JSONL file of gold QA records."""
    if not path.is_file():
        raise FileNotFoundError(f"Gold QA dataset file not found: {path}")

    items: list[GoldQAItem] = []
    lines = path.read_text(encoding="utf-8").splitlines()

    for idx, line in enumerate(lines, 1):
        line_clean = line.strip()
        if not line_clean:
            continue
        try:
            record = json.loads(line_clean)
        except Exception as e:
            raise ValueError(f"Line {idx}: Invalid JSON: {e}") from e

        valid, err = validate_gold_qa_item(record)
        if not valid:
            raise ValueError(f"Line {idx}: Gold validation error: {err}")

        items.append(
            GoldQAItem(
                id=record["id"],
                question=record["question"],
                reference_answer=record["reference_answer"],
                target_document_ids=[int(d) for d in record.get("target_document_ids", [])],
                gold_paragraph_nos=[int(p) for p in record.get("gold_paragraph_nos", [])],
                subject_area=record.get("subject_area", "statutory"),
                decision_year=int(record.get("decision_year", 2024)),
                reviewer_initials=record["reviewer_initials"],
                is_adversarial=record.get("is_adversarial", False),
                adversarial_category=record.get("adversarial_category"),
                disallow_tuning=True,
            )
        )

    return items


def export_gold_qa_file(items: list[GoldQAItem], path: Path) -> int:
    """Export GoldQAItems to standardized JSONL format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it.to_dict()) + "\n")
    return len(items)
