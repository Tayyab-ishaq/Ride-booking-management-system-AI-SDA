from __future__ import annotations
from datetime import datetime
from uuid import UUID
import asyncpg

from db.queries.auth_queries import SELECT_USER_BY_ID
from db.queries.driver_queries import (
    INSERT_DRIVER,
    SELECT_DRIVER_EARNINGS_SUMMARY,
    SELECT_DRIVER_BY_EMAIL,
    SELECT_DRIVER_BY_ID,
    SELECT_NEARBY_DRIVERS,
    SELECT_AVAILABLE_DRIVERS,
    UPDATE_DRIVER_AVAILABILITY,
    UPDATE_DRIVER_RATING,
)
from exception.driver_exceptions import DriverDatabaseSchemaError, DriverRepositoryError, DriverExists
from models.driver import Driver
import uuid
from db.queries.driver_queries import INSERT_VEHICLE


class DriverRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection

    async def get_by_id(self, driver_id: UUID) -> Driver | None:
        try:
            record = await self.connection.fetchrow(SELECT_DRIVER_BY_ID, driver_id)
        except asyncpg.UndefinedTableError as exc:
            raise DriverDatabaseSchemaError("Drivers table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise DriverRepositoryError("Failed to read driver from database") from exc
        if record is None:
            return None
        return Driver.from_record(record)

    async def get_by_email(self, email: str) -> Driver | None:
        try:
            record = await self.connection.fetchrow(SELECT_DRIVER_BY_EMAIL, email.lower())
        except asyncpg.UndefinedTableError as exc:
            raise DriverDatabaseSchemaError("Drivers table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise DriverRepositoryError("Failed to read driver from database") from exc
        if record is None:
            return None
        return Driver.from_record(record)

    async def create(self, driver: Driver) -> Driver:
        try:
            # Insert driver-specific fields and link to the user via user_id
            record = await self.connection.fetchrow(
                INSERT_DRIVER,
                driver.id,
                driver.id,  # user_id should match the user id (legacy behavior)
                driver.full_name,
                driver.email,
                driver.password_hash,
                driver.role.value,
                driver.created_at,
                driver.updated_at,
                driver.license_number,
                driver.vehicle_number,
                driver.vehicle_type,
                float(driver.rating),
                driver.total_rides,
                driver.is_available,
            )
        except asyncpg.UniqueViolationError as exc:
            # Unique violation likely means a driver/user with this identity already exists
            raise DriverExists("Driver with this id or unique field already exists") from exc
        except asyncpg.UndefinedTableError as exc:
            raise DriverDatabaseSchemaError("Drivers table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise DriverRepositoryError("Failed to create driver in database") from exc
        if record is None:
            raise DriverRepositoryError("Failed to create driver - no id returned")

        # Fetch the full joined driver+user record
        created_id = record["id"]
        try:
            joined = await self.connection.fetchrow(SELECT_DRIVER_BY_ID, created_id)
        except asyncpg.PostgresError as exc:
            raise DriverRepositoryError("Failed to read created driver from database") from exc
        if joined is None:
            raise DriverRepositoryError("Failed to fetch created driver")
        return Driver.from_record(joined)

    async def get_available_drivers(self) -> list[Driver]:
        try:
            records = await self.connection.fetch(SELECT_AVAILABLE_DRIVERS)
        except asyncpg.UndefinedTableError as exc:
            raise DriverDatabaseSchemaError("Drivers table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise DriverRepositoryError("Failed to read available drivers from database") from exc
        return [Driver.from_record(record) for record in records]

    async def update_availability(self, driver_id: UUID, is_available: bool) -> Driver | None:
        try:
            record = await self.connection.fetchrow(UPDATE_DRIVER_AVAILABILITY, str(driver_id), is_available)
        except asyncpg.UndefinedTableError as exc:
            raise DriverDatabaseSchemaError("Drivers table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise DriverRepositoryError("Failed to update driver availability") from exc
        if record is None:
            return None
        # fetch full joined record
        joined = await self.connection.fetchrow(SELECT_DRIVER_BY_ID, record["id"])
        if joined is None:
            return None
        return Driver.from_record(joined)

    async def update_rating(self, driver_id: UUID, new_rating: float) -> Driver | None:
        try:
            record = await self.connection.fetchrow(UPDATE_DRIVER_RATING, driver_id, new_rating)
        except asyncpg.UndefinedTableError as exc:
            raise DriverDatabaseSchemaError("Drivers table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise DriverRepositoryError("Failed to update driver rating") from exc
        if record is None:
            return None
        joined = await self.connection.fetchrow(SELECT_DRIVER_BY_ID, driver_id)
        if joined is None:
            return None
        return Driver.from_record(joined)

    async def create_vehicle(self, driver_id: UUID, plate_no: str, make_model: str, color: str | None, vehicle_type: str) -> uuid.UUID:
        try:
            vehicle_id = uuid.uuid4()
            record = await self.connection.fetchrow(
                INSERT_VEHICLE,
                vehicle_id,
                plate_no,
                driver_id,
                make_model,
                color,
                vehicle_type,
            )
        except asyncpg.UniqueViolationError as exc:
            raise DriverExists("Vehicle with this plate number already exists") from exc
        except asyncpg.UndefinedTableError as exc:
            raise DriverDatabaseSchemaError("Vehicles table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise DriverRepositoryError("Failed to create vehicle in database") from exc
        if record is None:
            raise DriverRepositoryError("Failed to create vehicle - no id returned")
        return record["vehicle_id"]

    async def get_nearby_drivers(self, lat: float, lng: float, radius_km: float) -> list[dict]:
        try:
            records = await self.connection.fetch(SELECT_NEARBY_DRIVERS, lat, lng, radius_km)
            return [
                {
                    "driver_id": str(record["driver_id"]),
                    "full_name": record["full_name"],
                    "latitude": float(record["latitude"]),
                    "longitude": float(record["longitude"]),
                    "distance_km": float(record["distance_km"]),
                }
                for record in records
            ]
        except asyncpg.UndefinedTableError as exc:
            raise DriverDatabaseSchemaError("Driver locations table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise DriverRepositoryError("Failed to fetch nearby drivers") from exc

    async def get_driver_earnings(
        self,
        driver_id: UUID,
        from_ts: str | None = None,
        to_ts: str | None = None,
    ) -> dict:
        def _normalize_ts(value: str | None) -> str | None:
            if value is None:
                return None
            raw = str(value).strip()
            if not raw:
                return None
            if raw.endswith("Z"):
                raw = f"{raw[:-1]}+00:00"
            try:
                return datetime.fromisoformat(raw).isoformat()
            except ValueError:
                return None

        normalized_from = _normalize_ts(from_ts)
        normalized_to = _normalize_ts(to_ts)

        # Resolve `driver_id` input against either drivers.id or drivers.user_id
        try:
            resolved = await self.connection.fetchrow(
                "SELECT id FROM drivers WHERE id = $1 OR user_id = $1 LIMIT 1",
                str(driver_id),
            )
        except asyncpg.PostgresError as exc:
            raise DriverRepositoryError("Failed to resolve driver for earnings") from exc
        if not resolved:
            # Legacy data may contain driver-role users without a drivers row.
            # Return an empty summary instead of surfacing a 503 error.
            return {
                "driver_id": str(driver_id),
                "completed_rides": 0,
                "total_earnings": 0.0,
                "average_fare": 0.0,
                "from": normalized_from,
                "to": normalized_to,
            }

        resolved_driver_id = resolved["id"]
        try:
            summary = await self.connection.fetchrow(
                SELECT_DRIVER_EARNINGS_SUMMARY,
                resolved_driver_id,
                normalized_from,
                normalized_to,
            )
        except asyncpg.UndefinedColumnError:
            # Backward-compatible fallback for DBs that don't have `rides.fare` yet.
            count_only = await self.connection.fetchrow(
                """
                SELECT COUNT(*) FILTER (WHERE status = 'completed') AS completed_rides
                FROM rides
                WHERE driver_id = $1
                  AND ($2::timestamptz IS NULL OR updated_at >= $2::timestamptz)
                  AND ($3::timestamptz IS NULL OR updated_at <= $3::timestamptz)
                """,
                resolved_driver_id,
                normalized_from,
                normalized_to,
            )
            completed_rides = 0
            if count_only is not None and count_only["completed_rides"] is not None:
                completed_rides = int(count_only["completed_rides"])
            summary = {
                "completed_rides": completed_rides,
                "total_earnings": 0,
                "average_fare": 0,
            }
        except asyncpg.PostgresError as exc:
            # If filtered query fails, fallback to unfiltered aggregate instead of 503.
            try:
                summary = await self.connection.fetchrow(
                    SELECT_DRIVER_EARNINGS_SUMMARY,
                    resolved_driver_id,
                    None,
                    None,
                )
                normalized_from = None
                normalized_to = None
            except asyncpg.PostgresError as fallback_exc:
                raise DriverRepositoryError("Failed to fetch driver earnings") from fallback_exc

        return {
            "driver_id": str(resolved_driver_id),
            "completed_rides": int(summary["completed_rides"] or 0),
            "total_earnings": float(summary["total_earnings"] or 0),
            "average_fare": float(summary["average_fare"] or 0),
            "from": normalized_from,
            "to": normalized_to,
        }
