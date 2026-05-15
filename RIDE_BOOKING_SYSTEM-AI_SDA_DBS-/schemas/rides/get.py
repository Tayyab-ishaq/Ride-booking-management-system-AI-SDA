from __future__ import annotations

from decimal import Decimal
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core.enums import RideStatus, RideType


class RideDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rider_id: UUID
    driver_id: UUID | None
    status: RideStatus
    origin: str
    destination: str
    ride_type: RideType
    fare: Decimal | None
    rating: int | None
    pickup_latitude: float | None
    pickup_longitude: float | None
    created_at: datetime
    updated_at: datetime
