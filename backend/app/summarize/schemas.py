"""Pydantic schemas for Structured Summarization (Task T-16 / FR-09)."""

from pydantic import BaseModel, Field


class SummaryRequest(BaseModel):
    document_id: int = Field(..., description="ID of document to summarize")
    max_sentences_per_section: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Target maximum number of sentences per rhetorical section",
    )


class SummarySentence(BaseModel):
    text: str = Field(..., description="Sentence text")
    source_para_nos: list[int] = Field(
        default_factory=list,
        description="Source judgment paragraph numbers anchoring this sentence",
    )
    supported: bool = Field(default=True, description="Whether citation verification verified passage support")
    support_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Verification lexical support overlap score")


class StructuredSummary(BaseModel):
    document_id: int
    case_title: str
    facts: list[SummarySentence] = Field(default_factory=list)
    issues: list[SummarySentence] = Field(default_factory=list)
    arguments: list[SummarySentence] = Field(default_factory=list)
    reasoning: list[SummarySentence] = Field(default_factory=list)
    holding: list[SummarySentence] = Field(default_factory=list)
    overall_faithfulness_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Fraction of summary sentences strictly verified against cited paragraphs",
    )
    total_sentences: int = 0
    supported_sentences: int = 0
    unsupported_sentences: int = 0
    disclaimer: str = Field(
        default="Informational research summary only. Not legal advice. Verify all points against official transcript.",
    )
