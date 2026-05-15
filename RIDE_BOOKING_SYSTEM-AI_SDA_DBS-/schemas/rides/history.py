from __future__ import annotations

from decimal import Decimal
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core.enums import RideStatus


class RideHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rider_id: UUID
    driver_id: UUID | None
    status: RideStatus
    origin: str
    destination: str
    fare: Decimal | None
    rating: int | None
    created_at: datetime
    updated_at: datetime


class RideHistoryResponse(BaseModel):
    rides: list[RideHistoryItem]
    total: int        # grand total count from DB — not just this page
    page: int
    page_size: int
