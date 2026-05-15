from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from models.user import User


@dataclass(slots=True)
class Driver(User):
    license_number: str
    vehicle_number: str
    vehicle_type: str
    rating: Decimal = Decimal('0.00')
    total_rides: int = 0
    is_available: bool = True

    @classmethod
    def from_record(cls, record: object) -> "Driver":
        # First create the base User object
        user = User.from_record(record)
        # Then extend it with Driver-specific fields
        return cls(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
            license_number=record["license_number"],
            vehicle_number=record["vehicle_number"],
            vehicle_type=record["vehicle_type"],
            rating=Decimal(str(record.get("rating", "0.00"))),
            total_rides=record.get("total_rides", 0),
            is_available=record.get("is_available", True),
        )
