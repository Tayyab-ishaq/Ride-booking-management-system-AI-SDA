from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from core.enums import UserRole
from core.security import hash_password
from exception.rider_exceptions import RiderExists
from models.rider import Rider
from repositories.rider_repository import RiderRepository
from schemas.rider.register import RiderRegisterRequest

from .base import RiderServiceBase


class RegisterRiderService(RiderServiceBase):
    async def register_rider(self, payload: RiderRegisterRequest) -> Rider:
        existing_rider = await self.repository.get_by_email(payload.email)
        if existing_rider is not None:
            raise RiderExists("Rider with this email already exists")

        now = datetime.now(timezone.utc)
        rider = Rider(
            id=uuid4(),
            full_name=payload.full_name,
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            role=UserRole.rider,
            created_at=now,
            updated_at=now,
            phone_number=payload.phone_number,
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
            payment_method=payload.payment_method or 'credit_card',
            wallet_balance=Decimal('0.00'),
            is_verified=False,
            total_rides=0,
            average_rating=Decimal('0.00'),
        )
        return await self.repository.create(rider)
