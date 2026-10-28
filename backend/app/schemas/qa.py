"""Pydantic schemas for Question Answering endpoints (Task T-11 / FR-05)."""

from pydantic import BaseModel, Field


class QARequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1500,
        description="Natural language Indian legal question",
    )
    court_codes: list[str] | None = Field(
        default=None,
        description="Optional court filters (e.g. ['sc', 'delhi_hc'])",
    )
    year_from: int | None = Field(
        default=None,
        ge=1950,
        description="Earliest judgment year filter",
    )
    year_to: int | None = Field(
        default=None,
        le=2030,
        description="Latest judgment year filter",
    )


class QACitation(BaseModel):
    marker: str = Field(..., description="Passage citation marker in text, e.g. [C1]")
    chunk_id: int
    document_id: int
    title: str
    court: str
    neutral_citation: str | None = None
    para_no: int | None = None
    snippet: str
    attribution: str


class QAResponse(BaseModel):
    question: str
    answer: str
    citations: list[QACitation]
    abstained: bool
    abstention_reason: str | None = None
    criminal_transition_notice: str | None = None
    disclaimer: str
    generation_status: str = Field(
        default="completed",
        description="Status: completed, abstained, or generation_unavailable",
    )
