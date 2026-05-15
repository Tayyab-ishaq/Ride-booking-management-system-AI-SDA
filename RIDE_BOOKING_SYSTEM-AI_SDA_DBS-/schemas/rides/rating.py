from __future__ import annotations

from typing import Annotated
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.enums import RideStatus


class RateDriverRequest(BaseModel):
    rating: Annotated[int, Field(ge=1, le=5)]


class RatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: RideStatus
    rating: int | None
    updated_at: datetime
