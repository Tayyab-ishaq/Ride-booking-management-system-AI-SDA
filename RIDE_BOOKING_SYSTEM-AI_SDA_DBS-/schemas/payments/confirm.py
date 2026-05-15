from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.enums import PaymentStatus


class ConfirmPaymentRequest(BaseModel):
    payment_id: UUID
    transaction_id: str | None = Field(default=None, max_length=255)


class ConfirmPaymentByPathRequest(BaseModel):
    transaction_id: str | None = Field(default=None, max_length=255)


class ConfirmPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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