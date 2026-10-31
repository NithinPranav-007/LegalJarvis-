"""Safety and legal-advice guardrails (Task T-20 / FR-17).

Enforces:
1. Refusal of requests for case-specific legal advice, personal litigation strategy, or client representation.
2. Refusal of illegal requests (evidence destruction, witness tampering, perjury, absconding).
3. Prohibition of personally identifiable information (PII) extraction regarding judicial officers or litigants.
4. Persistent statutory disclaimer compliance under Bar Council of India regulations.
"""

import re
from dataclasses import dataclass

PROHIBITED_PATTERNS = [
    # Perjury, false evidence, forgery
    (
        r"(?i)\b(how to (fabricate|forge|fake)|create (a fake|false) (affidavit|evidence|document)|bribe|destroy (the )?evidence|hide (the )?evidence)\b",
        "Assistance with illicit activities, forgery, or tampering with evidence is strictly prohibited.",
    ),
    # Absconding or evading legal process
    (
        r"(?i)\b(how (to|can i) (evade|escape|run away from) (arrest|police|the court|non-bailable warrant)|abscond)\b",
        "Assistance with evading lawful arrest or court process cannot be provided.",
    ),
    # Case-specific personal tactical advice
    (
        r"(?i)\b(should i (plead guilty|lie|confess)|guarantee (that )?i will win|promise (a )?bail|how do i get away with)\b",
        "Specific litigation strategy, guarantees of judicial outcomes, or advice on client confessions cannot be provided by an automated research tool.",
    ),
    # PII extraction for judges or litigants
    (
        r"(?i)\b(personal\s+(?:phone|mobile|cell|home\s+address|contact|whatsapp)(?:\s+number)?(?:\s+of)?\s+(?:the\s+)?(?:judge|justice|magistrate|litigant))\b",
        "Requests for private personal contact information of judicial officers or litigants are prohibited.",
    ),
]

BAR_COUNCIL_DISCLAIMER_REFUSAL = (
    "Needhi is an automated legal research and precedent retrieval assistant, not a licensed advocate. "
    "Under Bar Council of India rules and the Advocates Act, 1961, tailored legal advice, case strategy, or "
    "litigation assistance can only be provided by an advocate enrolled with a State Bar Council. "
    "Please consult an advocate for specific legal counsel."
)


@dataclass
class GuardrailResult:
    """Outcome of input safety guardrail evaluation."""

    is_safe: bool
    reason: str | None = None
    refusal_message: str | None = None


def check_input_guardrails(question: str) -> GuardrailResult:
    """Evaluate an inquiry against Indian legal ethics and safety rules."""
    q_stripped = question.strip()
    if not q_stripped:
        return GuardrailResult(
            is_safe=False,
            reason="Empty query",
            refusal_message="Please enter a valid legal research question.",
        )

    for pattern, rationale in PROHIBITED_PATTERNS:
        if re.search(pattern, q_stripped):
            return GuardrailResult(
                is_safe=False,
                reason=rationale,
                refusal_message=f"{rationale} {BAR_COUNCIL_DISCLAIMER_REFUSAL}",
            )

    return GuardrailResult(is_safe=True)
