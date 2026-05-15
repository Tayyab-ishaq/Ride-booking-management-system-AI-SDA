from __future__ import annotations

from typing import Annotated
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator, field_validator

from core.enums import UserRole


class RiderRegisterRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=60)
    last_name: str | None = Field(default=None, max_length=60)
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr
    password: Annotated[str, Field(min_length=6, max_length=128)]
    confirm_password: Annotated[str, Field(min_length=6, max_length=128)]
    phone_number: str | None = Field(default=None, max_length=20)
    emergency_contact_name: str | None = Field(default=None, max_length=120)
    emergency_contact_phone: str | None = Field(default=None, max_length=20)
    payment_method: str | None = Field(default='credit_card', max_length=50)

    @field_validator('password')
    def password_min_length(cls, v: str):
        if len(v or "") < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator('confirm_password')
    def confirm_password_min_length(cls, v: str):
        if len(v or "") < 6:
            raise ValueError("Confirm password must be at least 6 characters")
        return v

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> RiderRegisterRequest:
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm_password must match")
        if self.full_name is None:
            if not self.first_name:
                raise ValueError("first_name must be provided")
            parts = [self.first_name.strip()]
            if self.last_name:
                parts.append(self.last_name.strip())
            self.full_name = " ".join(part for part in parts if part).strip()
        return self


class RiderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr
    role: UserRole
    created_at: datetime
    updated_at: datetime
    phone_number: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    payment_method: str
    wallet_balance: Decimal
    is_verified: bool
    total_rides: int
    average_rating: Decimal
