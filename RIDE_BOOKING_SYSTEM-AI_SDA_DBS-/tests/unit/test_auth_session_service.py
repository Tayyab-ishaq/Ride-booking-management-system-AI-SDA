from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.config import Settings
from core.security import hash_password
from core.enums import UserRole
from exception.auth_exceptions import InvalidCredentials, TokenError
from models.user import User
from schemas.auth.session import LoginRequest
from services.auth import SessionAuthService


@dataclass
class FakeAuthRepository:
    user_by_email: dict[str, User] | None = None
    user_by_id: dict[UUID, User] | None = None

    def __post_init__(self) -> None:
        if self.user_by_email is None:
            self.user_by_email = {}
        if self.user_by_id is None:
            self.user_by_id = {}

    async def get_by_email(self, email: str) -> User | None:
        return self.user_by_email.get(email.lower())
    
    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.user_by_id.get(user_id)


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        database_url="postgresql://localhost/test",
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        access_token_expire_minutes=60,
        refresh_token_expire_minutes=1440,
    )


@pytest.fixture()
def repository() -> FakeAuthRepository:
    return FakeAuthRepository()


def build_user(email: str = "rider@example.com") -> User:
    return User(
        id=uuid4(),
        full_name="Test Rider",
        email=email,
        password_hash=hash_password("password123"),
        role=UserRole.rider,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio()
async def test_login_user_returns_tokens(repository: FakeAuthRepository, settings: Settings) -> None:
    service = SessionAuthService(repository, settings)
    repository.user_by_email["rider@example.com"] = build_user()

    response = await service.login_user(
        LoginRequest(email="rider@example.com", password="password123")
    )

    assert response.access_token
    assert response.refresh_token
    assert response.token_type == "bearer"


@pytest.mark.asyncio()
async def test_login_user_rejects_invalid_credentials(
    repository: FakeAuthRepository,
    settings: Settings,
) -> None:
    service = SessionAuthService(repository, settings)
    repository.user_by_email["rider@example.com"] = build_user()

    with pytest.raises(InvalidCredentials):
        await service.login_user(LoginRequest(email="rider@example.com", password="wrongpass123"))


@pytest.mark.asyncio()
async def test_refresh_access_token_returns_new_tokens(
    repository: FakeAuthRepository,
    settings: Settings,
) -> None:
    service = SessionAuthService(repository, settings)
    user = build_user()
    repository.user_by_email[user.email] = user
    repository.user_by_id[user.id] = user

    initial = await service.login_user(LoginRequest(email=user.email, password="password123"))
    refreshed = await service.refresh_access_token(initial.refresh_token)

    assert refreshed.access_token
    assert refreshed.refresh_token


@pytest.mark.asyncio()
async def test_refresh_access_token_rejects_invalid_token(
    repository: FakeAuthRepository,
    settings: Settings,
) -> None:
    service = SessionAuthService(repository, settings)

    with pytest.raises(TokenError):
        await service.refresh_access_token("not-a-token")


@pytest.mark.asyncio()
async def test_get_current_user_from_access_token(
    repository: FakeAuthRepository,
    settings: Settings,
) -> None:
    service = SessionAuthService(repository, settings)
    user = build_user()
    repository.user_by_email[user.email] = user
    repository.user_by_id[user.id] = user

    tokens = await service.login_user(LoginRequest(email=user.email, password="password123"))
    current = await service.get_current_user(tokens.access_token)

    assert current.email == user.email


@pytest.mark.asyncio()
async def test_logout_accepts_valid_refresh_token(
    repository: FakeAuthRepository,
    settings: Settings,
) -> None:
    service = SessionAuthService(repository, settings)
    user = build_user()
    repository.user_by_email[user.email] = user

    tokens = await service.login_user(LoginRequest(email=user.email, password="password123"))
    await service.logout(tokens.refresh_token)


@pytest.mark.asyncio()
async def test_refresh_rejects_revoked_token(
    repository: FakeAuthRepository,
    settings: Settings,
) -> None:
    service = SessionAuthService(repository, settings)
    user = build_user()
    repository.user_by_email[user.email] = user

    tokens = await service.login_user(LoginRequest(email=user.email, password="password123"))
    await service.logout(tokens.refresh_token)

    with pytest.raises(TokenError):
        await service.refresh_access_token(tokens.refresh_token)
