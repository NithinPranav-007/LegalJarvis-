"""Citation existence verification ensuring 100% citation grounding (Task T-12 / FR-06)."""

import re
from dataclasses import dataclass, field
from typing import Any

RE_CITATION_MARKER = re.compile(r"\[C(\d+)\]")


@dataclass
class ExistenceCheckResult:
    valid_markers: list[str] = field(default_factory=list)
    invalid_markers: list[str] = field(default_factory=list)
    is_valid: bool = True

    @property
    def has_hallucinations(self) -> bool:
        return len(self.invalid_markers) > 0


def verify_citation_existence(
    text: str,
    allowed_markers: set[str] | list[str] | dict[str, Any],
) -> ExistenceCheckResult:
    """Verify that every citation marker in the text exists in the allowed retrieval set.

    In LegalJarvis, no answer may reference a passage marker [C{i}] that was not
    explicitly provided in the context.
    """
    allowed_set = set(allowed_markers)
    found_matches = RE_CITATION_MARKER.finditer(text)

    valid: list[str] = []
    invalid: list[str] = []

    for m in found_matches:
        marker = f"[C{m.group(1)}]"
        if marker in allowed_set:
            if marker not in valid:
                valid.append(marker)
        else:
            if marker not in invalid:
                invalid.append(marker)

    return ExistenceCheckResult(
        valid_markers=valid,
        invalid_markers=invalid,
        is_valid=(len(invalid) == 0),
    )
