"""Rhetorical role segmenter model and IL-TUR RR evaluation interface (Task T-16 / FR-09)."""

import re
from typing import Any

from app.ingest.segment import classify_segment

RHETORICAL_ROLES = ["facts", "issues", "arguments", "reasoning", "holding", "other"]

IL_TUR_RR_LABEL_MAP = {
    "facts": "facts",
    "issue": "issues",
    "issues": "issues",
    "argument": "arguments",
    "arguments": "arguments",
    "analysis": "reasoning",
    "reasoning": "reasoning",
    "ratio of the decision": "reasoning",
    "precedent": "reasoning",
    "statute": "reasoning",
    "holding": "holding",
    "order": "holding",
    "ruling by present court": "holding",
    "ruling by lower court": "facts",
}


class RhetoricalSegmenter:
    """Rhetorical role segmenter for Indian judgments."""

    def __init__(self) -> None:
        self.rules_enabled = True

    def predict_role(self, text: str, para_no: int | None = None) -> str:
        """Classify a paragraph or passage into one of the 5 canonical rhetorical roles."""
        clean = text.strip()
        if not clean:
            return "other"

        # Check explicit heading cues
        lower_snippet = clean[:300].lower()
        if re.search(r"\b(brief\s+facts|factual\s+background|facts\s+of\s+the\s+case|prosecution\s+case)\b", lower_snippet):
            return "facts"
        if re.search(r"\b(questions?\s+of\s+law|point\s+for\s+determination|issue\s+framed)\b", lower_snippet):
            return "issues"
        if re.search(r"\b(contentions?\s+of|submitted\s+that|learned\s+counsel\s+argued|argued\s+by)\b", lower_snippet):
            return "arguments"
        if re.search(r"\b(we\s+have\s+considered|in\s+our\s+considered\s+view|it\s+is\s+clear\s+from|doctrine|interpretation)\b", lower_snippet):
            return "reasoning"
        if re.search(r"\b(in\s+the\s+result|appeal\s+is\s+(allowed|dismissed)|we\s+hold\s+that|order\s+accordingly)\b", lower_snippet):
            return "holding"

        # Fallback to T-06 heuristic segment detector
        return classify_segment(clean)

    def evaluate_on_dataset(self, gold_examples: list[dict[str, Any]]) -> dict[str, float]:
        """Evaluate segmenter macro-F1 against gold rhetorical role labels."""
        if not gold_examples:
            return {"macro_f1": 0.0, "accuracy": 0.0, "total": 0}

        true_positives: dict[str, int] = {r: 0 for r in RHETORICAL_ROLES}
        false_positives: dict[str, int] = {r: 0 for r in RHETORICAL_ROLES}
        false_negatives: dict[str, int] = {r: 0 for r in RHETORICAL_ROLES}
        total_correct = 0

        for ex in gold_examples:
            text = ex["text"]
            raw_gold = str(ex["label"]).lower().strip()
            gold_role = IL_TUR_RR_LABEL_MAP.get(raw_gold, "other")
            pred_role = self.predict_role(text, para_no=ex.get("para_no"))

            if pred_role == gold_role:
                true_positives[pred_role] += 1
                total_correct += 1
            else:
                false_positives[pred_role] += 1
                false_negatives[gold_role] += 1

        gold_roles_present = {
            IL_TUR_RR_LABEL_MAP.get(str(ex["label"]).lower().strip(), "other") for ex in gold_examples
        }
        f1_scores = []
        for r in gold_roles_present:
            tp = true_positives[r]
            fp = false_positives[r]
            fn = false_negatives[r]
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            f1_scores.append(f1)

        macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
        accuracy = total_correct / len(gold_examples)

        return {
            "macro_f1": round(macro_f1, 4),
            "accuracy": round(accuracy, 4),
            "total": len(gold_examples),
        }
