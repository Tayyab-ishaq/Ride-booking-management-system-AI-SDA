from __future__ import annotations

from uuid import UUID

from exception.ride_exceptions import RideNotFound, RideOwnershipError
from models.ride import Ride

from .base import RideServiceBase


class RideLifecycleService(RideServiceBase):

    async def accept_ride(self, ride_id: UUID, driver_id: UUID) -> Ride:
        """Driver accepts a requested ride — assigns them and moves status to accepted."""
        return await self.repository.assign_driver(ride_id, driver_id)

    async def start_ride(self, ride_id: UUID, driver_id: UUID) -> Ride:
        """Driver marks the ride as in progress — verifies ownership, then DB guards the transition."""
        ride = await self.repository.get_by_id(ride_id)
        if ride is None:
            raise RideNotFound(f"Ride {ride_id} not found")
        if ride.driver_id != driver_id:
            raise RideOwnershipError("You are not the assigned driver for this ride")
        return await self.repository.start_ride(ride_id)

    async def complete_ride(self, ride_id: UUID, driver_id: UUID) -> Ride:
        """Driver marks the ride as completed — verifies ownership, then DB guards the transition."""
        ride = await self.repository.get_by_id(ride_id)
        if ride is None:
            raise RideNotFound(f"Ride {ride_id} not found")
        if ride.driver_id != driver_id:
            raise RideOwnershipError("You are not the assigned driver for this ride")
        return await self.repository.complete_ride(ride_id)

    async def cancel_ride(self, ride_id: UUID) -> Ride:
        """Rider or driver cancels the ride — only valid from requested or accepted."""
        return await self.repository.cancel(ride_id)

    async def get_ride(self, ride_id: UUID) -> Ride:
        """Fetch a single ride by id, raise if not found."""
        ride = await self.repository.get_by_id(ride_id)
        if ride is None:
            raise RideNotFound(f"Ride {ride_id} not found")
        return ride
