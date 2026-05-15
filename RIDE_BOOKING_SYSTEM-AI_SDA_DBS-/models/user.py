from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core.enums import UserRole


@dataclass(slots=True)
class User:
    id: UUID
    full_name: str
    email: str
    password_hash: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, record: object) -> "User":
        return cls(
            id=record["id"],
            full_name=record["full_name"],
            email=record["email"],
            password_hash=record["password_hash"],
            role=UserRole(record["role"]),
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )
