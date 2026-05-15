from __future__ import annotations

from uuid import UUID
from decimal import Decimal

import asyncpg

from db.queries.payment_queries import (
    INSERT_PAYMENT,
    INSERT_PAYMENT_METHOD,
    SELECT_PAYMENT_BY_ID,
    SELECT_PAYMENT_METHOD_BY_ID,
    SELECT_PAYMENT_METHODS_BY_USER_ID,
    SELECT_PAYMENT_BY_RIDE_ID,
    SELECT_PAYMENTS_BY_USER_ID,
    SELECT_PAYMENT_BY_TRANSACTION_ID,
    SELECT_PAYMENTS_BY_USER_PAGINATED,
    COUNT_PAYMENTS_BY_USER,
    SET_DEFAULT_PAYMENT_METHOD,
    UPDATE_PAYMENT_STATUS,
    UPDATE_PAYMENT_TRANSACTION_ID,
    DELETE_PAYMENT_METHOD_BY_ID,
    DELETE_PAYMENT_BY_ID,
    ARCHIVE_PAYMENT,
)
from exception.payment_exceptions import (
    PaymentNotFound,
    PaymentAlreadyProcessed,
    PaymentDatabaseSchemaError,
    PaymentRepositoryError,
    InvalidPaymentStatus,
)
from models.payment import Payment
from models.payment_method import PaymentMethod


class PaymentRepository:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self.connection = connection

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    async def create_payment(
        self,
        payment_id: UUID,
        ride_id: UUID,
        user_id: UUID,
        amount: Decimal,
        status: str,
        payment_method: str,
        transaction_id: str | None = None,
        created_at = None,
        updated_at = None,
    ) -> Payment:
        """Create a new payment record"""
        try:
            from datetime import datetime, timezone
            created_at = created_at or datetime.now(timezone.utc)
            updated_at = updated_at or datetime.now(timezone.utc)
            
            record = await self.connection.fetchrow(
                INSERT_PAYMENT,
                payment_id,
                ride_id,
                user_id,
                amount,
                status,
                payment_method,
                transaction_id,
                created_at,
                updated_at,
            )
            
            if not record:
                raise PaymentDatabaseSchemaError(
                    "Failed to create payment: no record returned"
                )
            
            return Payment.from_record(record)
        except asyncpg.UniqueViolationError:
            raise PaymentAlreadyProcessed(f"Payment {payment_id} already exists")
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(f"Failed to create payment: {str(e)}")

    async def update_payment_status(
        self, payment_id: UUID, status: str
    ) -> Payment:
        """Update payment status"""
        try:
            from datetime import datetime, timezone
            updated_at = datetime.now(timezone.utc)
            
            record = await self.connection.fetchrow(
                UPDATE_PAYMENT_STATUS, status, updated_at, payment_id
            )
            
            if not record:
                raise PaymentNotFound(f"Payment {payment_id} not found")
            
            return Payment.from_record(record)
        except PaymentNotFound:
            raise
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(f"Failed to update payment status: {str(e)}")

    async def update_transaction_id(
        self, payment_id: UUID, transaction_id: str
    ) -> Payment:
        """Update transaction ID"""
        try:
            from datetime import datetime, timezone
            updated_at = datetime.now(timezone.utc)
            
            record = await self.connection.fetchrow(
                UPDATE_PAYMENT_TRANSACTION_ID,
                transaction_id,
                updated_at,
                payment_id,
            )
            
            if not record:
                raise PaymentNotFound(f"Payment {payment_id} not found")
            
            return Payment.from_record(record)
        except PaymentNotFound:
            raise
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(
                f"Failed to update transaction ID: {str(e)}"
            )

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    async def get_payment_by_id(self, payment_id: UUID) -> Payment:
        """Get payment by ID"""
        try:
            record = await self.connection.fetchrow(
                SELECT_PAYMENT_BY_ID, payment_id
            )
            
            if not record:
                raise PaymentNotFound(f"Payment {payment_id} not found")
            
            return Payment.from_record(record)
        except PaymentNotFound:
            raise
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(f"Failed to get payment: {str(e)}")

    async def get_payment_by_ride_id(self, ride_id: UUID) -> Payment:
        """Get payment by ride ID"""
        try:
            record = await self.connection.fetchrow(
                SELECT_PAYMENT_BY_RIDE_ID, ride_id
            )
            
            if not record:
                raise PaymentNotFound(f"Payment for ride {ride_id} not found")
            
            return Payment.from_record(record)
        except PaymentNotFound:
            raise
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(f"Failed to get payment by ride: {str(e)}")

    async def get_payments_by_user_id(self, user_id: UUID) -> list[Payment]:
        """Get all payments by user ID"""
        try:
            records = await self.connection.fetch(
                SELECT_PAYMENTS_BY_USER_ID, user_id
            )
            
            return [Payment.from_record(record) for record in records]
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(
                f"Failed to get payments by user: {str(e)}"
            )

    async def get_payment_by_transaction_id(
        self, transaction_id: str
    ) -> Payment:
        """Get payment by transaction ID"""
        try:
            record = await self.connection.fetchrow(
                SELECT_PAYMENT_BY_TRANSACTION_ID, transaction_id
            )
            
            if not record:
                raise PaymentNotFound(
                    f"Payment with transaction {transaction_id} not found"
                )
            
            return Payment.from_record(record)
        except PaymentNotFound:
            raise
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(
                f"Failed to get payment by transaction ID: {str(e)}"
            )

    async def get_payments_paginated(
        self, user_id: UUID, limit: int, offset: int
    ) -> list[Payment]:
        """Get paginated payments for a user"""
        try:
            records = await self.connection.fetch(
                SELECT_PAYMENTS_BY_USER_PAGINATED, user_id, limit, offset
            )
            
            return [Payment.from_record(record) for record in records]
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(
                f"Failed to get paginated payments: {str(e)}"
            )

    async def count_payments_by_user(self, user_id: UUID) -> int:
        """Count payments by user"""
        try:
            record = await self.connection.fetchval(
                COUNT_PAYMENTS_BY_USER, user_id
            )
            
            return record or 0
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(
                f"Failed to count payments: {str(e)}"
            )

    # ------------------------------------------------------------------ #
    # Delete                                                               #
    # ------------------------------------------------------------------ #

    async def delete_payment(self, payment_id: UUID) -> None:
        """Delete payment"""
        try:
            await self.connection.execute(DELETE_PAYMENT_BY_ID, payment_id)
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(f"Failed to delete payment: {str(e)}")

    async def archive_payment(self, payment_id: UUID) -> None:
        """Archive payment (soft delete)"""
        try:
            from datetime import datetime, timezone
            deleted_at = datetime.now(timezone.utc)
            
            await self.connection.execute(ARCHIVE_PAYMENT, deleted_at, payment_id)
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(f"Failed to archive payment: {str(e)}")

    # ------------------------------------------------------------------ #
    # Payment methods                                                     #
    # ------------------------------------------------------------------ #

    async def create_payment_method(
        self,
        method_id: UUID,
        user_id: UUID,
        method_type: str,
        token_ref: str,
        is_default: bool,
    ) -> PaymentMethod:
        from datetime import datetime, timezone

        created_at = datetime.now(timezone.utc)
        updated_at = created_at
        try:
            record = await self.connection.fetchrow(
                INSERT_PAYMENT_METHOD,
                method_id,
                user_id,
                method_type,
                token_ref,
                is_default,
                created_at,
                updated_at,
            )
            if record is None:
                raise PaymentRepositoryError("Failed to create payment method")
            if is_default:
                await self.connection.execute(SET_DEFAULT_PAYMENT_METHOD, user_id, method_id)
            return PaymentMethod.from_record(record)
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(f"Failed to create payment method: {str(e)}")

    async def get_payment_method_by_id(self, method_id: UUID) -> PaymentMethod:
        try:
            record = await self.connection.fetchrow(SELECT_PAYMENT_METHOD_BY_ID, method_id)
            if not record:
                raise PaymentNotFound(f"Payment method {method_id} not found")
            return PaymentMethod.from_record(record)
        except PaymentNotFound:
            raise
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(f"Failed to read payment method: {str(e)}")

    async def get_payment_methods_by_user_id(self, user_id: UUID) -> list[PaymentMethod]:
        try:
            records = await self.connection.fetch(SELECT_PAYMENT_METHODS_BY_USER_ID, user_id)
            return [PaymentMethod.from_record(record) for record in records]
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(f"Failed to list payment methods: {str(e)}")

    async def delete_payment_method(self, method_id: UUID, user_id: UUID) -> None:
        try:
            deleted = await self.connection.execute(DELETE_PAYMENT_METHOD_BY_ID, method_id, user_id)
            if deleted == "DELETE 0":
                raise PaymentNotFound(f"Payment method {method_id} not found")
        except PaymentNotFound:
            raise
        except asyncpg.PostgresError as e:
            raise PaymentRepositoryError(f"Failed to delete payment method: {str(e)}")
