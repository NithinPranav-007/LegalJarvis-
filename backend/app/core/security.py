"""Cryptographic security, password hashing, and JWT token management (Task T-13 / FR-15)."""

import datetime
from typing import Any

import bcrypt
from jose import JWTError, jwt  # type: ignore[import-untyped]

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash password securely using bcrypt with auto-generated salt."""
    if not password:
        raise ValueError("Password cannot be empty.")
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    data: dict[str, Any],
    expires_delta: datetime.timedelta | None = None,
) -> str:
    """Generate signed JWT access token with expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.UTC) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate JWT access token signature and expiration."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None
