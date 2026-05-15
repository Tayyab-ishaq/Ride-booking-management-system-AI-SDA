from __future__ import annotations

from uuid import UUID
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentMethodRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    token: str = Field(min_length=1, max_length=255)
    method_type: Literal["card", "wallet", "cash"] = Field(alias="type")
    is_default: bool = False


class PaymentMethodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    method_type: str
    token_ref: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
