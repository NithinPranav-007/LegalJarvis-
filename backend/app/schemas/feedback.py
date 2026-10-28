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


class ClaimVerdict(BaseModel):
    claim_index: int
    claim_text: str
    is_supported: bool
    cited_para_no: int | None = None
    issue_type: Literal["supported", "unsupported", "hallucinated", "wrong_law"] = "supported"
    notes: str | None = None


class ReviewerFeedbackCreate(BaseModel):
    answer_id: int
    rating: int = Field(ge=1, le=5, description="1 to 5 overall quality rating")
    overall_label: Literal["supported", "unsupported", "hallucinated", "incomplete", "wrong_law"]
    claims: list[ClaimVerdict] = Field(default_factory=list)
    legal_accuracy_notes: str | None = None
    reviewer_role: str | None = "advocate"


class FeedbackExportItem(BaseModel):
    id: int
    answer_id: int
    user_id: int | None
    rating: int | None
    label: str | None
    comment: str | None
    reviewer_role: str | None
    claims_json: dict | list | None = None
    created_at: str
