from __future__ import annotations

from uuid import UUID

import asyncpg

from db.queries.ride_queries import (
    ACCEPT_MATCHED_RIDE,
    ASSIGN_DRIVER,
    CANCEL_RIDE,
    COMPLETE_RIDE,
    COUNT_RIDES_BY_DRIVER,
    COUNT_RIDES_BY_RIDER,
    FIND_AVAILABLE_DRIVER,
    FIND_AVAILABLE_DRIVER_EXCLUDE,
    FIND_AVAILABLE_DRIVERS_FOR_MATCHING,
    GET_AVAILABLE_DRIVER_BY_ID,
    INSERT_RIDE,
    RESET_DRIVER_ASSIGNMENT,
    SELECT_ACTIVE_RIDE_BY_RIDER,
    SELECT_ACTIVE_RIDE_BY_DRIVER,
    SELECT_RIDE_BY_ID,
    SELECT_RIDES_BY_DRIVER_PAGINATED,
    SELECT_RIDES_BY_RIDER_PAGINATED,
    START_RIDE,
    UPDATE_DRIVER_RATING,
    ARCHIVE_RIDE,
    DELETE_RIDE_BY_ID,
)
from exception.ride_exceptions import (
    RideAlreadyCancelled,
    RideAlreadyRated,
    RideDatabaseSchemaError,
    RideNotFound,
    RideRepositoryError,
    InvalidRideTransition,
)
from models.ride import Ride


class RideRepository:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self.connection = connection

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    async def create(self, ride: Ride) -> Ride:
        try:
            record = await self.connection.fetchrow(
                INSERT_RIDE,
                ride.id,
                ride.rider_id,
                ride.status.value,
                ride.origin,
                ride.destination,
                ride.ride_type.value,
                ride.fare,
                ride.pickup_latitude,
                ride.pickup_longitude,
            )
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to create ride in database") from exc
        if record is None:
            raise RideRepositoryError("Failed to create ride in database")
        return Ride.from_record(record)

    async def assign_driver(self, ride_id: UUID, driver_id: UUID) -> Ride:
        try:
            record = await self.connection.fetchrow(ASSIGN_DRIVER, ride_id, driver_id)
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to assign driver to ride") from exc
        if record is None:
            raise RideNotFound(
                f"Ride {ride_id} not found or is no longer in 'requested' status"
            )
        return Ride.from_record(record)

    async def accept_matched_ride(self, ride_id: UUID, driver_id: UUID) -> Ride:
        try:
            record = await self.connection.fetchrow(ACCEPT_MATCHED_RIDE, ride_id, driver_id)
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to accept matched ride") from exc
        if record is None:
            raise InvalidRideTransition(
                f"Ride {ride_id} cannot be accepted — it must be in 'offered' status for this driver"
            )
        return Ride.from_record(record)

    async def start_ride(self, ride_id: UUID) -> Ride:
        """Transition: accepted → in_progress. SQL guard ensures status is 'accepted'."""
        try:
            record = await self.connection.fetchrow(START_RIDE, ride_id)
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to start ride") from exc
        if record is None:
            raise InvalidRideTransition(
                f"Ride {ride_id} cannot be started — it must be in 'accepted' status"
            )
        return Ride.from_record(record)

    async def complete_ride(self, ride_id: UUID) -> Ride:
        """Transition: in_progress → completed. SQL guard ensures status is 'in_progress'."""
        try:
            record = await self.connection.fetchrow(COMPLETE_RIDE, ride_id)
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to complete ride") from exc
        if record is None:
            raise InvalidRideTransition(
                f"Ride {ride_id} cannot be completed — it must be in 'in_progress' status"
            )
        return Ride.from_record(record)

    async def cancel(self, ride_id: UUID) -> Ride:
        try:
            record = await self.connection.fetchrow(CANCEL_RIDE, ride_id)
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to cancel ride") from exc
        if record is None:
            raise RideAlreadyCancelled(
                f"Ride {ride_id} not found or cannot be cancelled in its current status"
            )
        return Ride.from_record(record)

    async def rate_driver(self, ride_id: UUID, rating: int, rider_id: UUID) -> Ride:
        try:
            record = await self.connection.fetchrow(
                UPDATE_DRIVER_RATING, ride_id, rating, rider_id
            )
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to save driver rating") from exc
        if record is None:
            raise RideAlreadyRated(
                f"Ride {ride_id} not found, not completed, already rated, or not your ride"
            )
        return Ride.from_record(record)

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    async def get_by_id(self, ride_id: UUID) -> Ride | None:
        try:
            record = await self.connection.fetchrow(SELECT_RIDE_BY_ID, ride_id)
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to read ride from database") from exc
        if record is None:
            return None
        return Ride.from_record(record)

    async def get_history_by_rider(
        self, rider_id: UUID, limit: int, offset: int
    ) -> tuple[list[Ride], int]:
        try:
            records = await self.connection.fetch(
                SELECT_RIDES_BY_RIDER_PAGINATED, rider_id, limit, offset
            )
            total = await self.connection.fetchval(COUNT_RIDES_BY_RIDER, rider_id)
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to read ride history from database") from exc
        return [Ride.from_record(r) for r in records], int(total or 0)

    async def get_history_by_driver(
        self, driver_id: UUID, limit: int, offset: int
    ) -> tuple[list[Ride], int]:
        try:
            records = await self.connection.fetch(
                SELECT_RIDES_BY_DRIVER_PAGINATED, driver_id, limit, offset
            )
            total = await self.connection.fetchval(COUNT_RIDES_BY_DRIVER, driver_id)
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to read ride history from database") from exc
        return [Ride.from_record(r) for r in records], int(total or 0)

    async def get_active_ride_by_rider(self, rider_id: UUID) -> Ride | None:
        try:
            record = await self.connection.fetchrow(
                SELECT_ACTIVE_RIDE_BY_RIDER, rider_id
            )
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to check active ride") from exc
        if record is None:
            return None
        return Ride.from_record(record)

    async def get_active_ride_by_driver(self, driver_id: UUID) -> Ride | None:
        try:
            record = await self.connection.fetchrow(
                SELECT_ACTIVE_RIDE_BY_DRIVER, driver_id
            )
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to check active driver ride") from exc
        if record is None:
            return None
        return Ride.from_record(record)

    async def find_available_driver(self) -> UUID | None:
        try:
            record = await self.connection.fetchrow(FIND_AVAILABLE_DRIVER)
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Users table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to search for an available driver") from exc
        if record is None:
            return None
        return record["id"]

    async def reset_driver_assignment(self, ride_id: UUID, driver_id: UUID) -> Ride:
        """Reset driver assignment - driver rejected the ride. Ride goes back to 'requested' status."""
        try:
            record = await self.connection.fetchrow(
                RESET_DRIVER_ASSIGNMENT, ride_id, driver_id
            )
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to reset driver assignment") from exc
        if record is None:
            raise InvalidRideTransition(
                f"Ride {ride_id} cannot be rejected - invalid status or driver mismatch"
            )
        return Ride.from_record(record)

    async def reject_driver_and_find_new_driver(
        self, ride_id: UUID, driver_id: UUID
    ) -> Ride:
        """Reject a matched ride and immediately attempt to rematch a new available driver."""
        try:
            async with self.connection.transaction():
                record = await self.connection.fetchrow(
                    RESET_DRIVER_ASSIGNMENT, ride_id, driver_id
                )
                if record is None:
                    raise InvalidRideTransition(
                        f"Ride {ride_id} cannot be rejected - invalid status or driver mismatch"
                    )

                new_driver = await self.connection.fetchrow(
                    FIND_AVAILABLE_DRIVER_EXCLUDE, driver_id
                )
                if new_driver is None:
                    return Ride.from_record(record)

                assigned = await self.connection.fetchrow(
                    ASSIGN_DRIVER,
                    ride_id,
                    new_driver["id"],
                )
                if assigned is None:
                    raise RideRepositoryError(
                        "Failed to assign a replacement driver after rejection"
                    )
                return Ride.from_record(assigned)
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides or users table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to process driver rejection and rematch") from exc

    async def archive_and_delete(self, ride_id: UUID) -> None:
        """Archive a ride into `ride_history` and remove it from `rides`.

        Runs both operations inside a DB transaction to avoid data loss.
        """
        try:
            async with self.connection.transaction():
                archived = await self.connection.fetchrow(ARCHIVE_RIDE, ride_id)
                if archived is None:
                    # nothing to archive — treat as no-op
                    return
                await self.connection.execute(DELETE_RIDE_BY_ID, ride_id)
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Rides or ride_history table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to archive and delete ride") from exc

    async def get_available_drivers_for_matching(
        self, exclude_driver_id: UUID | None = None
    ) -> list[dict]:
        """Get all available drivers for ride matching.
        
        Returns drivers who are not currently assigned to any active ride.
        
        Args:
            exclude_driver_id: Optional driver ID to exclude from results (e.g., for rematch)
            
        Returns:
            List of driver dicts with keys: id, full_name, email, rating, total_rides
        """
        try:
            records = await self.connection.fetch(
                FIND_AVAILABLE_DRIVERS_FOR_MATCHING,
                exclude_driver_id,
            )
            return [dict(record) for record in records]
        except asyncpg.UndefinedTableError as exc:
            raise RideDatabaseSchemaError(
                "Drivers table is missing. Run DB migrations first."
            ) from exc
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to fetch available drivers") from exc

    async def get_driver_by_id(self, driver_id: UUID) -> dict | None:
        """Get driver info by ID, checking availability.
        
        Args:
            driver_id: Driver UUID
            
        Returns:
            Driver dict or None if not found or not available
        """
        try:
            record = await self.connection.fetchrow(
                GET_AVAILABLE_DRIVER_BY_ID,
                driver_id,
            )
            return dict(record) if record else None
        except asyncpg.PostgresError as exc:
            raise RideRepositoryError("Failed to fetch driver") from exc
