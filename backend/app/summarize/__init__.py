"""Structured summarization and rhetorical role segmentation package (Task T-16 / FR-09)."""

from app.summarize.schemas import StructuredSummary, SummaryRequest
from app.summarize.summarizer import StructuredSummarizer

__all__ = [
    "StructuredSummarizer",
    "StructuredSummary",
    "SummaryRequest",
]
