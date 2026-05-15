from __future__ import annotations

from uuid import UUID

from app.config import Settings
from core.enums import RideStatus
from exception.ride_exceptions import (
    DriverNotAvailable,
    InvalidRideTransition,
    RideNotFound,
    RideOwnershipError,
)
from models.ride import Ride
from repositories.ride_repository import RideRepository
from services.rides.ranking import LocalRankingProvider, RankedDriver

from .base import RideServiceBase


class RideMatchingService(RideServiceBase):
    """Service for matching riders with drivers using ranking algorithm.
    
    Workflow:
    1. Fetch available drivers from database
    2. Rank drivers using scoring algorithm (distance, rating, experience, etc.)
    3. Assign top-ranked driver to ride
    4. Handle rejections by trying next in ranked list
    """

    def __init__(
        self,
        repository: RideRepository,
        settings: Settings,
        ranking_provider: LocalRankingProvider | None = None,
    ):
        super().__init__(repository, settings)
        # Support dependency injection for ranking provider
        # This allows swapping in n8n webhook provider later
        self.ranking_provider = ranking_provider or LocalRankingProvider()
        # Store ranked drivers for rematch on rejection
        self._ride_driver_rankings: dict[UUID, list[RankedDriver]] = {}

    async def find_driver_for_ride(self, ride_id: UUID, rider_id: UUID) -> Ride:
        """Find and assign best-ranked driver for a ride.
        
        Algorithm:
        1. Validate ride exists and belongs to rider
        2. Fetch available drivers
        3. Rank drivers by score (distance, rating, experience, acceptance rate)
        4. Assign top-ranked driver
        5. Store ranked list for potential rematch on rejection
        
        Args:
            ride_id: The ride to match
            rider_id: The rider requesting the match
            
        Returns:
            Updated Ride with assigned driver
            
        Raises:
            RideNotFound: Ride doesn't exist
            RideOwnershipError: Rider doesn't own this ride
            InvalidRideTransition: Ride not in 'requested' status
            DriverNotAvailable: No drivers available for matching
        """
        ride = await self.repository.get_by_id(ride_id)
        if ride is None:
            raise RideNotFound(f"Ride {ride_id} not found")
        if ride.rider_id != rider_id:
            raise RideOwnershipError("You are not the owner of this ride request")
        if ride.status != RideStatus.requested:
            raise InvalidRideTransition(
                "Driver search can only be started for rides in requested status"
            )
        
        # Validate pickup coordinates exist
        if ride.pickup_latitude is None or ride.pickup_longitude is None:
            raise InvalidRideTransition(
                "Ride must have pickup location for driver matching"
            )

        # Fetch available drivers
        available_drivers = await self.repository.get_available_drivers_for_matching()
        if not available_drivers:
            raise DriverNotAvailable("No available drivers at the moment")

        # Rank drivers using ranking provider
        ranked_drivers = await self.ranking_provider.rank_drivers(ride, available_drivers)
        if not ranked_drivers:
            raise DriverNotAvailable("No nearby drivers available")

        # Store ranked list for rematch on rejection
        self._ride_driver_rankings[ride_id] = ranked_drivers

        # Assign top-ranked driver
        best_driver = ranked_drivers[0]
        return await self.repository.assign_driver(ride_id, best_driver.driver_id)

    async def driver_accept_matched_ride(self, ride_id: UUID, driver_id: UUID) -> Ride:
        """Driver confirms acceptance of a matched ride offer.
        
        This is the final confirmation after driver has been matched and notified.
        
        Args:
            ride_id: The ride to accept
            driver_id: The driver accepting
            
        Returns:
            Updated Ride
            
        Raises:
            RideNotFound: Ride doesn't exist
            RideOwnershipError: Driver not assigned to this ride
            InvalidRideTransition: Ride not in 'accepted' status
        """
        ride = await self.repository.get_by_id(ride_id)
        if ride is None:
            raise RideNotFound(f"Ride {ride_id} not found")
        if ride.driver_id != driver_id:
            raise RideOwnershipError(
                "You are not the assigned driver for this ride"
            )
        if ride.status != RideStatus.offered:
            raise InvalidRideTransition(
                f"Can only accept rides in 'offered' status, current status is '{ride.status}'"
            )
        
        # Clean up stored rankings since ride was accepted
        self._ride_driver_rankings.pop(ride_id, None)

        return await self.repository.accept_matched_ride(ride_id, driver_id)

    async def driver_reject_matched_ride(self, ride_id: UUID, driver_id: UUID) -> Ride:
        """Driver rejects a matched ride and tries next ranked driver.
        
        If ranked drivers exist, automatically attempts to assign the next one.
        Otherwise, goes back to 'requested' status for fresh matching attempt.
        
        Args:
            ride_id: The ride to reject
            driver_id: The driver rejecting
            
        Returns:
            Updated Ride (either with new driver assigned or back in 'requested')
            
        Raises:
            RideNotFound: Ride doesn't exist
            RideOwnershipError: Driver not assigned to this ride
            InvalidRideTransition: Ride not in 'accepted' status
        """
        ride = await self.repository.get_by_id(ride_id)
        if ride is None:
            raise RideNotFound(f"Ride {ride_id} not found")
        if ride.driver_id != driver_id:
            raise RideOwnershipError(
                "You are not the assigned driver for this ride"
            )
        if ride.status != RideStatus.offered:
            raise InvalidRideTransition(
                f"Can only reject rides in 'offered' status, current status is '{ride.status}'"
            )

        # Reset driver assignment (ride goes back to 'requested')
        reset_ride = await self.repository.reset_driver_assignment(ride_id, driver_id)

        # Try to assign next ranked driver if we have a ranking for this ride
        ranked_drivers = self._ride_driver_rankings.get(ride_id)
        if ranked_drivers and len(ranked_drivers) > 1:
            # Remove the rejected driver from the list
            remaining = [d for d in ranked_drivers if d.driver_id != driver_id]
            
            if remaining:
                # Try next driver
                next_driver = remaining[0]
                self._ride_driver_rankings[ride_id] = remaining
                try:
                    return await self.repository.assign_driver(ride_id, next_driver.driver_id)
                except Exception:
                    # If assignment fails, return ride in 'requested' status
                    # Caller can retry matching
                    return reset_ride

        # No more ranked drivers, clear the ranking
        self._ride_driver_rankings.pop(ride_id, None)
        return reset_ride

    async def get_matching_status(self, ride_id: UUID, rider_id: UUID) -> Ride:
        """Get current status of driver matching for a ride (polling endpoint).
        
        Riders can poll this endpoint to see if a driver has been matched/accepted.
        
        Args:
            ride_id: The ride to check
            rider_id: The rider who owns the ride
            
        Returns:
            Current Ride object
            
        Raises:
            RideNotFound: Ride doesn't exist
            RideOwnershipError: Rider doesn't own this ride
        """
        ride = await self.repository.get_by_id(ride_id)
        if ride is None:
            raise RideNotFound(f"Ride {ride_id} not found")
        if ride.rider_id != rider_id:
            raise RideOwnershipError("You are not the owner of this ride request")
        return ride
