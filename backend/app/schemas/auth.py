"""Authentication and user schemas (Task T-13 / FR-15)."""

from typing import Literal

from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, description="User email address")
    password: str = Field(
        ..., min_length=8, max_length=128, description="User password (min 8 characters)"
    )
    role: Literal["researcher", "citizen", "reviewer", "admin"] = Field(
        default="researcher",
        description="Assigned RBAC role",
    )


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    role: str


class UserProfileResponse(BaseModel):
    id: int
    email: str
    role: str
    created_at: str
