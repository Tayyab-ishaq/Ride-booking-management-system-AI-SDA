from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class PaymentMethod:
    id: UUID
    user_id: UUID
    method_type: str
    token_ref: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, record: object) -> "PaymentMethod":
        return cls(
            id=record["id"],
            user_id=record["user_id"],
            method_type=record["method_type"],
            token_ref=record["token_ref"],
            is_default=record["is_default"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )
