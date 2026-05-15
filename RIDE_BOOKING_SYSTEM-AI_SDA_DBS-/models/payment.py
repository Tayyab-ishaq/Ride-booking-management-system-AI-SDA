from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from core.enums import PaymentStatus


@dataclass(slots=True)
class Payment:
    id: UUID
    ride_id: UUID
    user_id: UUID
    amount: Decimal
    status: PaymentStatus
    payment_method: str
    transaction_id: str | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, record: object) -> "Payment":
        return cls(
            id=record["id"],
            ride_id=record["ride_id"],
            user_id=record["user_id"],
            amount=record["amount"],
            status=PaymentStatus(record["status"]),
            payment_method=record["payment_method"],
            transaction_id=record.get("transaction_id"),
            deleted_at=record.get("deleted_at"),
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )