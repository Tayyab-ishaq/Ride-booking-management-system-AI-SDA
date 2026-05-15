from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from core.enums import PaymentStatus, RideStatus, RideType
from exception.payment_exceptions import (
    InvalidPaymentMethod,
    InvalidPaymentStatus,
    PaymentAlreadyProcessed,
    PaymentNotFound,
    PaymentOwnershipError,
)
from repositories.ride_repository import RideRepository
from services.payments.base import PaymentServiceBase

logger = logging.getLogger(__name__)


class PaymentCreateService(PaymentServiceBase):
    """Service for creating payments"""

    SUPPORTED_METHODS = {"card", "wallet", "cash"}
    BASE_FARES = {
        RideType.ridex: Decimal("4.20"),
        RideType.ridexl: Decimal("6.80"),
        RideType.comfort: Decimal("9.50"),
    }

    def __init__(self, repository, settings, ride_repository: RideRepository | None = None):
        super().__init__(repository, settings)
        self._ride_repository = ride_repository

    async def create_payment(
        self,
        ride_id: UUID,
        user_id: UUID,
        amount: Decimal,
        payment_method: str,
    ):
        """Create a pending internal payment for a completed rider-owned ride."""
        from uuid import uuid4

        normalized_method = payment_method.strip().lower()
        # Accept method UUIDs from stored payment methods, otherwise expect a literal method.
        try:
            method_id = UUID(normalized_method)
            stored_method = await self.repository.get_payment_method_by_id(method_id)
            if stored_method.user_id != user_id:
                raise InvalidPaymentMethod("Selected payment method does not belong to this user")
            normalized_method = stored_method.method_type
        except ValueError:
            pass
        except Exception:
            raise

        if normalized_method not in self.SUPPORTED_METHODS:
            raise InvalidPaymentMethod(
                f"Unsupported payment method '{payment_method}'. Supported methods: card, wallet, cash."
            )

        ride_repository = self._ride_repository or RideRepository(self.repository.connection)
        ride = await ride_repository.get_by_id(ride_id)
        if ride is None:
            raise PaymentNotFound(f"Ride {ride_id} not found")
        if ride.rider_id != user_id:
            raise PaymentOwnershipError("You are not allowed to create payment for this ride")
        if ride.status != RideStatus.completed:
            raise InvalidPaymentStatus("Payment can only be initiated after ride completion")

        try:
            existing_payment = await self.repository.get_payment_by_ride_id(ride_id)
            raise PaymentAlreadyProcessed(
                f"Payment {existing_payment.id} already exists for ride {ride_id}"
            )
        except PaymentNotFound:
            pass

        charge_amount = ride.fare
        if charge_amount is None:
            try:
                charge_amount = self.BASE_FARES[ride.ride_type]
                logger.info(
                    "payment_amount_fallback_to_ride_type ride_id=%s user_id=%s ride_type=%s amount=%s",
                    ride_id,
                    user_id,
                    ride.ride_type,
                    charge_amount,
                )
            except KeyError as exc:
                raise ValueError(
                    f"Ride fare is missing for ride {ride_id} and ride type {ride.ride_type} is unsupported"
                ) from exc

        if amount != charge_amount:
            logger.info(
                "payment_amount_adjusted_to_ride_fare ride_id=%s user_id=%s requested_amount=%s fare=%s",
                ride_id,
                user_id,
                amount,
                charge_amount,
            )

        payment_id = uuid4()
        payment = await self.repository.create_payment(
            payment_id=payment_id,
            ride_id=ride_id,
            user_id=user_id,
            amount=charge_amount,
            status=PaymentStatus.pending.value,
            payment_method=normalized_method,
            transaction_id=None,
        )

        return payment
