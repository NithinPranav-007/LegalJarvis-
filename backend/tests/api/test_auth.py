"""Authentication, JWT tokens, and RBAC role matrix tests (Task T-13 / FR-15)."""

import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.search import get_sync_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.models import Base
from app.main import app


@pytest.fixture
def auth_db() -> Session:
    """In-memory database for authentication tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


def test_password_hashing_and_verification() -> None:
    raw_pwd = "LegalJarvisSecurePass123!"
    hashed = hash_password(raw_pwd)

    assert hashed != raw_pwd
    assert hashed.startswith("$2")  # Standard bcrypt format
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_creation_and_expiration() -> None:
    # 1. Valid token
    payload = {"sub": "42", "email": "lawyer@example.com", "role": "researcher"}
    token = create_access_token(payload, expires_delta=datetime.timedelta(minutes=5))
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "42"
    assert decoded["email"] == "lawyer@example.com"
    assert decoded["role"] == "researcher"

    # 2. Expired token
    expired_token = create_access_token(payload, expires_delta=datetime.timedelta(seconds=-10))
    decoded_expired = decode_access_token(expired_token)
    assert decoded_expired is None

    # 3. Invalid / tampered token
    assert decode_access_token("invalid.jwt.token") is None


@pytest.mark.asyncio
async def test_user_registration_and_login_flow(auth_db: Session) -> None:
    def override_db():
        yield auth_db

    app.dependency_overrides[get_sync_db] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register new researcher
        reg_resp = await client.post(
            "/v1/auth/register",
            json={
                "email": "advocate.sharma@example.com",
                "password": "Password123!",
                "role": "researcher",
            },
        )
        assert reg_resp.status_code == 201
        reg_data = reg_resp.json()
        assert "access_token" in reg_data
        assert reg_data["role"] == "researcher"

        # 2. Duplicate registration rejected
        dup_resp = await client.post(
            "/v1/auth/register",
            json={
                "email": "advocate.sharma@example.com",
                "password": "Password123!",
                "role": "researcher",
            },
        )
        assert dup_resp.status_code == 400

        # 3. Successful login
        login_resp = await client.post(
            "/v1/auth/login",
            json={
                "email": "advocate.sharma@example.com",
                "password": "Password123!",
            },
        )
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        assert "access_token" in login_data
        token = login_data["access_token"]

        # 4. Failed login (wrong password)
        bad_login = await client.post(
            "/v1/auth/login",
            json={
                "email": "advocate.sharma@example.com",
                "password": "IncorrectPassword!",
            },
        )
        assert bad_login.status_code == 401

        # 5. Access profile with token
        headers = {"Authorization": f"Bearer {token}"}
        me_resp = await client.get("/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["email"] == "advocate.sharma@example.com"
        assert me_data["role"] == "researcher"

        # 6. Access profile without token -> 401
        unauth_resp = await client.get("/v1/auth/me")
        assert unauth_resp.status_code == 401

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rbac_role_matrix(auth_db: Session) -> None:
    def override_db():
        yield auth_db

    app.dependency_overrides[get_sync_db] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create users for all 4 roles
        roles = ["researcher", "citizen", "reviewer", "admin"]
        tokens: dict[str, str] = {}

        for role in roles:
            resp = await client.post(
                "/v1/auth/register",
                json={
                    "email": f"{role}@legaljarvis.local",
                    "password": "Password123!",
                    "role": role,
                },
            )
            assert resp.status_code == 201
            tokens[role] = resp.json()["access_token"]

        # Test Admin-only endpoint: /v1/auth/admin/ping
        # 1. Researcher -> 403
        r_resp = await client.get(
            "/v1/auth/admin/ping",
            headers={"Authorization": f"Bearer {tokens['researcher']}"},
        )
        assert r_resp.status_code == 403

        # 2. Citizen -> 403
        c_resp = await client.get(
            "/v1/auth/admin/ping",
            headers={"Authorization": f"Bearer {tokens['citizen']}"},
        )
        assert c_resp.status_code == 403

        # 3. Reviewer -> 403
        rev_resp = await client.get(
            "/v1/auth/admin/ping",
            headers={"Authorization": f"Bearer {tokens['reviewer']}"},
        )
        assert rev_resp.status_code == 403

        # 4. Admin -> 200
        admin_resp = await client.get(
            "/v1/auth/admin/ping",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert admin_resp.status_code == 200
        assert admin_resp.json()["status"] == "ok"

    app.dependency_overrides.clear()
