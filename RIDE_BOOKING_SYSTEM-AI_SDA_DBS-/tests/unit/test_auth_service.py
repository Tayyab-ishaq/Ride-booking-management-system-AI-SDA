from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.config import Settings
from core.enums import UserRole
from exception.auth_exceptions import UserExists
from models.user import User
from schemas.auth.register import RegisterRequest
from services.auth import RegisterAuthService


@dataclass
class FakeAuthRepository:
    user_by_email: dict[str, User] | None = None

    def __post_init__(self) -> None:
        if self.user_by_email is None:
            self.user_by_email = {}

    async def get_by_email(self, email: str) -> User | None:
        return self.user_by_email.get(email.lower())

    async def create(self, user: User) -> User:
        self.user_by_email[user.email] = user
        return User(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        database_url="postgresql://localhost/test",
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        access_token_expire_minutes=60,
    )


@pytest.fixture()
def repository() -> FakeAuthRepository:
    return FakeAuthRepository()


@pytest.mark.asyncio()
async def test_register_user_hashes_password(repository: FakeAuthRepository, settings: Settings) -> None:
    service = RegisterAuthService(repository, settings)
    payload = RegisterRequest(
        full_name="Test Rider",
        email="rider@example.com",
        password="password123",
        confirm_password="password123",
    )

    user = await service.register_user(payload)

    assert user.email == "rider@example.com"
    assert user.password_hash != payload.password
    assert user.role == UserRole.rider


@pytest.mark.asyncio()
async def test_register_user_rejects_duplicates(repository: FakeAuthRepository, settings: Settings) -> None:
    service = RegisterAuthService(repository, settings)
    existing = User(
        id=uuid4(),
        full_name="Existing User",
        email="existing@example.com",
        password_hash="$2b$12$example",
        role=UserRole.rider,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repository.user_by_email[existing.email] = existing

    payload = RegisterRequest(
        full_name="Existing User",
        email=existing.email,
        password="password123",
        confirm_password="password123",
    )

    with pytest.raises(UserExists):
        await service.register_user(payload)


def test_register_request_rejects_password_mismatch() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            full_name="Mismatch User",
            email="mismatch@example.com",
            password="password123",
            confirm_password="different123",
        )
