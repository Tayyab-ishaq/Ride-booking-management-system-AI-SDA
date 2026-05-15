from __future__ import annotations
from uuid import UUID
import asyncpg

from db.queries.rider_queries import (
    INSERT_RIDER,
    SELECT_RIDER_BY_EMAIL,
    SELECT_RIDER_BY_ID,
    SELECT_VERIFIED_RIDERS,
    UPDATE_RIDER_VERIFICATION,
    UPDATE_RIDER_WALLET,
    UPDATE_RIDER_RATING,
)
from exception.rider_exceptions import RiderDatabaseSchemaError, RiderRepositoryError
from models.rider import Rider


class RiderRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection

    async def get_by_id(self, rider_id: UUID) -> Rider | None:
        try:
            record = await self.connection.fetchrow(SELECT_RIDER_BY_ID, rider_id)
        except asyncpg.UndefinedTableError as exc:
            raise RiderDatabaseSchemaError("Riders table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise RiderRepositoryError("Failed to read rider from database") from exc
        if record is None:
            return None
        return Rider.from_record(record)

    async def get_by_email(self, email: str) -> Rider | None:
        try:
            record = await self.connection.fetchrow(SELECT_RIDER_BY_EMAIL, email.lower())
        except asyncpg.UndefinedTableError as exc:
            raise RiderDatabaseSchemaError("Riders table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise RiderRepositoryError("Failed to read rider from database") from exc
        if record is None:
            return None
        return Rider.from_record(record)

    async def create(self, rider: Rider) -> Rider:
        try:
            record = await self.connection.fetchrow(
                INSERT_RIDER,
                rider.id,
                rider.full_name,
                rider.email,
                rider.password_hash,
                rider.role.value,
                rider.phone_number,
                rider.emergency_contact_name,
                rider.emergency_contact_phone,
                rider.payment_method,
                float(rider.wallet_balance),
                rider.is_verified,
                rider.total_rides,
                float(rider.average_rating),
            )
        except asyncpg.UniqueViolationError as exc:
            raise RiderRepositoryError("Email already exists") from exc
        except asyncpg.UndefinedTableError as exc:
            raise RiderDatabaseSchemaError("Riders table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise RiderRepositoryError("Failed to create rider in database") from exc
        if record is None:
            raise RiderRepositoryError("Failed to create rider - no record returned")
        return Rider.from_record(record)

    async def get_verified_riders(self) -> list[Rider]:
        try:
            records = await self.connection.fetch(SELECT_VERIFIED_RIDERS)
        except asyncpg.UndefinedTableError as exc:
            raise RiderDatabaseSchemaError("Riders table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise RiderRepositoryError("Failed to read verified riders from database") from exc
        return [Rider.from_record(record) for record in records]

    async def update_verification(self, rider_id: UUID, is_verified: bool) -> Rider | None:
        try:
            record = await self.connection.fetchrow(UPDATE_RIDER_VERIFICATION, rider_id, is_verified)
        except asyncpg.UndefinedTableError as exc:
            raise RiderDatabaseSchemaError("Riders table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise RiderRepositoryError("Failed to update rider verification") from exc
        if record is None:
            return None
        return Rider.from_record(record)

    async def update_wallet(self, rider_id: UUID, wallet_balance: float) -> Rider | None:
        try:
            record = await self.connection.fetchrow(UPDATE_RIDER_WALLET, rider_id, wallet_balance)
        except asyncpg.UndefinedTableError as exc:
            raise RiderDatabaseSchemaError("Riders table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise RiderRepositoryError("Failed to update rider wallet") from exc
        if record is None:
            return None
        return Rider.from_record(record)

    async def update_rating(self, rider_id: UUID, new_rating: float) -> Rider | None:
        try:
            record = await self.connection.fetchrow(UPDATE_RIDER_RATING, rider_id, new_rating)
        except asyncpg.UndefinedTableError as exc:
            raise RiderDatabaseSchemaError("Riders table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise RiderRepositoryError("Failed to update rider rating") from exc
        if record is None:
            return None
        return Rider.from_record(record)
