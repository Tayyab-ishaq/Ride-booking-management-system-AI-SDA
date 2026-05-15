from __future__ import annotations

from uuid import UUID

from models.ride import Ride
from schemas.rides.rating import RateDriverRequest

from .base import RideServiceBase


class DriverRatingService(RideServiceBase):

    async def rate_driver(
        self, ride_id: UUID, payload: RateDriverRequest, rider_id: UUID
    ) -> Ride:
        """Rider submits a 1–5 star rating for their completed ride."""
        return await self.repository.rate_driver(ride_id, payload.rating, rider_id)
