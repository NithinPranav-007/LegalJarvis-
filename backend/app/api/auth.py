"""Authentication and RBAC API router (Task T-13 / FR-15)."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.models import User
from app.db.session import get_sync_db
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
)

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])
security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    db: Session = Depends(get_sync_db),
) -> User:
    """Dependency extracting and verifying authenticated user from Bearer JWT."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(auth.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalar(select(User).filter_by(id=int(user_id)))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_optional_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    db: Session = Depends(get_sync_db),
) -> User | None:
    """Optional dependency extracting user from Bearer JWT without raising 401 if unauthenticated."""
    if not auth or not auth.credentials:
        return None
    payload = decode_access_token(auth.credentials)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return db.scalar(select(User).filter_by(id=int(user_id)))


def require_role(*allowed_roles: str):
    """Dependency factory checking user role against allowed RBAC roles."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: role '{current_user.role}' lacks required permissions ({allowed_roles}).",
            )
        return current_user

    return role_checker


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserRegisterRequest,
    db: Session = Depends(get_sync_db),
) -> TokenResponse:
    """Register a new user account with hashed password and return access token."""
    existing = db.scalar(select(User).filter_by(email=payload.email.lower().strip()))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    user = User(
        email=payload.email.lower().strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
    return TokenResponse(
        access_token=token,
        token_type="bearer",  # nosec B106
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        role=user.role,
    )


@router.post("/login", response_model=TokenResponse)
def login_user(
    payload: UserLoginRequest,
    db: Session = Depends(get_sync_db),
) -> TokenResponse:
    """Authenticate email and password, returning JWT access token."""
    user = db.scalar(select(User).filter_by(email=payload.email.lower().strip()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
    return TokenResponse(
        access_token=token,
        token_type="bearer",  # nosec B106
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        role=user.role,
    )


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    """Get profile of current authenticated user."""
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        created_at=str(current_user.created_at),
    )


@router.get("/admin/ping", dependencies=[Depends(require_role("admin"))])
def admin_only_check() -> dict[str, str]:
    """Test endpoint accessible strictly by admin role."""
    return {"status": "ok", "message": "Admin authorization verified."}
