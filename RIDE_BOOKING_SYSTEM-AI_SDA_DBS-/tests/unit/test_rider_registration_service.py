from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.config import Settings
from core.enums import UserRole
from exception.rider_exceptions import RiderExists
from models.rider import Rider
from schemas.rider.register import RiderRegisterRequest
from services.rider import RegisterRiderService


@dataclass
class FakeRiderRepository:
    user_by_email: dict[str, Rider] | None = None

    def __post_init__(self) -> None:
        if self.user_by_email is None:
            self.user_by_email = {}

    async def get_by_email(self, email: str) -> Rider | None:
        return self.user_by_email.get(email.lower())

    async def create(self, rider: Rider) -> Rider:
        self.user_by_email[rider.email] = rider
        return Rider(
            id=rider.id,
            full_name=rider.full_name,
            email=rider.email,
            password_hash=rider.password_hash,
            role=rider.role,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            phone_number=rider.phone_number,
            emergency_contact_name=rider.emergency_contact_name,
            emergency_contact_phone=rider.emergency_contact_phone,
            payment_method=rider.payment_method,
            wallet_balance=rider.wallet_balance,
            is_verified=rider.is_verified,
            total_rides=rider.total_rides,
            average_rating=rider.average_rating,
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
def repository() -> FakeRiderRepository:
    return FakeRiderRepository()


@pytest.mark.asyncio()
async def test_register_rider_hashes_password(repository: FakeRiderRepository, settings: Settings) -> None:
    service = RegisterRiderService(repository, settings)
    payload = RiderRegisterRequest(
        full_name="Test Rider",
        email="rider@example.com",
        password="password123",
        confirm_password="password123",
        phone_number="+1234567890",
    )

    rider = await service.register_rider(payload)

    assert rider.email == "rider@example.com"
    assert rider.password_hash != payload.password
    assert rider.role == UserRole.rider
    assert rider.is_verified == False
    assert rider.wallet_balance == 0


@pytest.mark.asyncio()
async def test_register_rider_rejects_duplicates(repository: FakeRiderRepository, settings: Settings) -> None:
    service = RegisterRiderService(repository, settings)
    existing = Rider(
        id=uuid4(),
        full_name="Existing Rider",
        email="existing@example.com",
        password_hash="$2b$12$example",
        role=UserRole.rider,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repository.user_by_email[existing.email] = existing

    payload = RiderRegisterRequest(
        full_name="Existing Rider",
        email=existing.email,
        password="password123",
        confirm_password="password123",
    )

    with pytest.raises(RiderExists):
        await service.register_rider(payload)


def test_rider_register_request_rejects_password_mismatch() -> None:
    with pytest.raises(ValidationError):
        RiderRegisterRequest(
            full_name="Mismatch Rider",
            email="mismatch@example.com",
            password="password123",
            confirm_password="different123",
        )


def test_rider_register_request_accepts_optional_fields() -> None:
    payload = RiderRegisterRequest(
        full_name="Optional Rider",
        email="optional@example.com",
        password="password123",
        confirm_password="password123",
        phone_number=None,
        emergency_contact_name=None,
    )
    assert payload.phone_number is None
    assert payload.emergency_contact_name is None
    assert payload.payment_method == "credit_card"
