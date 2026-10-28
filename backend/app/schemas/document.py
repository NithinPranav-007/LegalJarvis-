"""Pydantic schemas for Document and Case Viewer endpoints (Task T-14 / FR-05)."""

from pydantic import BaseModel, Field


class ChunkOut(BaseModel):
    id: int
    para_no: int | None = None
    segment_type: str | None = None
    text: str
    start_char: int
    end_char: int


class DocumentDetail(BaseModel):
    id: int
    title: str
    court_code: str
    court_name: str | None = None
    decision_date: str | None = None
    neutral_citation: str | None = None
    bench: str | None = None
    dataset_name: str
    extraction_quality: float | None = None
    text: str = Field(..., description="Full cleaned text of judgment")
    chunks: list[ChunkOut] = Field(default_factory=list, description="Ordered chunks/paragraphs")
    attribution: str = Field(
        default="Supreme Court judgments released under Open Government Data (OGD) / Creative Commons Attribution (CC-BY 4.0).",
        description="Dataset attribution notice",
    )
