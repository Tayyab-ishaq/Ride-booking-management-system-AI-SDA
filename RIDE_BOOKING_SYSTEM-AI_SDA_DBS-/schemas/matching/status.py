from __future__ import annotations

from decimal import Decimal
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core.enums import RideStatus


class MatchingStatusResponse(BaseModel):
    """Response model for polling match progress"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "rider_id": "550e8400-e29b-41d4-a716-446655440001",
                "driver_id": "550e8400-e29b-41d4-a716-446655440002",
                "status": "accepted",
                "origin": "123 Main St",
                "destination": "456 Oak Ave",
                "fare": 25.50,
                "created_at": "2026-05-09T10:00:00Z",
                "updated_at": "2026-05-09T10:05:00Z",
                "matched_at": None,
            }
        }
    )

    id: UUID
    rider_id: UUID
    driver_id: UUID | None
    status: RideStatus
    origin: str
    destination: str
    fare: Decimal | None
    created_at: datetime
    updated_at: datetime
    matched_at: datetime | None = None
