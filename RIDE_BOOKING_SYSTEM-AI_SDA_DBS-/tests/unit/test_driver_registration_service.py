from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.config import Settings
from core.enums import UserRole
from exception.driver_exceptions import DriverExists
from models.user import User
from schemas.driver.register import DriverRegisterRequest
from services.driver import RegisterDriverService


@dataclass
class FakeDriverRepository:
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
def repository() -> FakeDriverRepository:
    return FakeDriverRepository()


@pytest.mark.asyncio()
async def test_register_driver_hashes_password(repository: FakeDriverRepository, settings: Settings) -> None:
    service = RegisterDriverService(repository, settings)
    payload = DriverRegisterRequest(
        full_name="Test Driver",
        email="driver@example.com",
        password="password123",
        confirm_password="password123",
        license_number="DL12345",
        vehicle_number="ABC1234",
        vehicle_type="sedan",
    )

    driver = await service.register_driver(payload)

    assert driver.email == "driver@example.com"
    assert driver.password_hash != payload.password
    assert driver.role == UserRole.driver


@pytest.mark.asyncio()
async def test_register_driver_rejects_duplicates(repository: FakeDriverRepository, settings: Settings) -> None:
    service = RegisterDriverService(repository, settings)
    existing = User(
        id=uuid4(),
        full_name="Existing Driver",
        email="existing@example.com",
        password_hash="$2b$12$example",
        role=UserRole.driver,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repository.user_by_email[existing.email] = existing

    payload = DriverRegisterRequest(
        full_name="Existing Driver",
        email=existing.email,
        password="password123",
        confirm_password="password123",
        license_number="DL12345",
        vehicle_number="ABC1234",
        vehicle_type="sedan",
    )

    with pytest.raises(DriverExists):
        await service.register_driver(payload)


def test_driver_register_request_rejects_password_mismatch() -> None:
    with pytest.raises(ValidationError):
        DriverRegisterRequest(
            full_name="Mismatch Driver",
            email="mismatch@example.com",
            password="password123",
            confirm_password="different123",
            license_number="DL12345",
            vehicle_number="ABC1234",
            vehicle_type="sedan",
        )


def test_driver_register_request_rejects_missing_license() -> None:
    with pytest.raises(ValidationError):
        DriverRegisterRequest(
            full_name="Missing License Driver",
            email="missing@example.com",
            password="password123",
            confirm_password="password123",
            license_number="",
            vehicle_number="ABC1234",
            vehicle_type="sedan",
        )


def test_driver_register_request_rejects_missing_vehicle() -> None:
    with pytest.raises(ValidationError):
        DriverRegisterRequest(
            full_name="Missing Vehicle Driver",
            email="missing@example.com",
            password="password123",
            confirm_password="password123",
            license_number="DL12345",
            vehicle_number="",
            vehicle_type="sedan",
        )
