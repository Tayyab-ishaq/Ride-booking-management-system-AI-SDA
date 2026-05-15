from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from models.user import User


@dataclass(slots=True)
class Rider(User):
    phone_number: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    payment_method: str = 'credit_card'
    wallet_balance: Decimal = Decimal('0.00')
    is_verified: bool = False
    total_rides: int = 0
    average_rating: Decimal = Decimal('0.00')

    @classmethod
    def from_record(cls, record: object) -> "Rider":
        # First create the base User object
        user = User.from_record(record)
        # Then extend it with Rider-specific fields
        return cls(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
            phone_number=record.get("phone_number"),
            emergency_contact_name=record.get("emergency_contact_name"),
            emergency_contact_phone=record.get("emergency_contact_phone"),
            payment_method=record.get("payment_method", "credit_card"),
            wallet_balance=Decimal(str(record.get("wallet_balance", "0.00"))),
            is_verified=record.get("is_verified", False),
            total_rides=record.get("total_rides", 0),
            average_rating=Decimal(str(record.get("average_rating", "0.00"))),
        )
