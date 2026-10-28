"""Pydantic schemas for Feedback endpoints (Task T-14 / FR-14)."""

from typing import Literal

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    answer_id: int | None = Field(default=None, description="Optional answer ID if persisted")
    query: str | None = Field(default=None, description="The query being evaluated")
    rating: int = Field(
        ..., description="User rating: 1 for thumbs-up/helpful, -1 for thumbs-down/unhelpful"
    )
    label: Literal["supported", "unsupported", "hallucinated", "incomplete", "wrong_law"] | None = (
        Field(
            default=None,
            description="Categorical reason for rating",
        )
    )
    notes: str | None = Field(
        default=None, max_length=2000, description="User comments or critique"
    )


class FeedbackResponse(BaseModel):
    id: int
    status: str
    message: str
