from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.enums import PaymentStatus


class PaymentInitiateRequest(BaseModel):
    ride_id: UUID
    amount: Decimal = Field(gt=0)
    payment_method: str = Field(default="cash", max_length=50)


class PaymentInitiateResponse(BaseModel):
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