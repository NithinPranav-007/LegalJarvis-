"""Schemas for search endpoints (Task T-07 / FR-04)."""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Natural language search query")
    court_codes: list[str] | None = Field(default=None, description="Optional court filter codes (e.g. ['sc', 'delhi_hc'])")
    year_from: int | None = Field(default=None, ge=1950, description="Earliest judgment year")
    year_to: int | None = Field(default=None, le=2030, description="Latest judgment year")
    limit: int = Field(default=20, ge=1, le=100, description="Page limit")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class SearchItem(BaseModel):
    chunk_id: int
    document_id: int
    title: str
    court: str
    decision_date: str | None = None
    neutral_citation: str | None = None
    para_no: int | None = None
    segment_type: str | None = None
    snippet: str
    score: float
    attribution: str


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchItem]
    attribution: str
