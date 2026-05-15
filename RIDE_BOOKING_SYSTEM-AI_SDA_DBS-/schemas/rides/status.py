from __future__ import annotations

from decimal import Decimal
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core.enums import RideStatus


class RideStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    driver_id: UUID | None
    status: RideStatus
    fare: Decimal | None
    updated_at: datetime
