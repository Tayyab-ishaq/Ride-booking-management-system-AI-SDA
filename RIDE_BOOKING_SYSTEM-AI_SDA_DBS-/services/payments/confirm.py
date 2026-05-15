from __future__ import annotations

from uuid import UUID, uuid4

from core.enums import PaymentStatus
from exception.payment_exceptions import (
    InvalidPaymentStatus,
    PaymentOwnershipError,
)
from services.payments.base import PaymentServiceBase


class PaymentConfirmService(PaymentServiceBase):
    """Service for confirming payments"""

    async def confirm_payment(
        self,
        payment_id: UUID,
        user_id: UUID,
        transaction_id: str | None = None,
    ):
        """Confirm a pending payment with an internal transaction identifier."""
        payment = await self.repository.get_payment_by_id(payment_id)

        if payment.user_id != user_id:
            raise PaymentOwnershipError("You are not allowed to confirm this payment")

        if payment.status == PaymentStatus.completed:
            return payment

        if payment.status not in (PaymentStatus.pending, PaymentStatus.processing):
            raise InvalidPaymentStatus(
                f"Cannot confirm payment with status {payment.status.value}"
            )

        resolved_transaction_id = transaction_id or f"INT-{uuid4().hex[:12].upper()}"
        if payment.transaction_id != resolved_transaction_id:
            await self.repository.update_transaction_id(payment_id, resolved_transaction_id)

        confirmed = await self.repository.update_payment_status(
            payment_id, PaymentStatus.completed.value
        )
        if hasattr(self.repository, "connection"):
            await self.repository.connection.execute(
                """
                UPDATE drivers d
                SET total_earnings = COALESCE(d.total_earnings, 0) + $2,
                    updated_at = NOW()
                FROM rides r
                WHERE r.id = $1
                  AND r.driver_id = d.id
                  AND r.status = 'completed'
                """,
                confirmed.ride_id,
                confirmed.amount,
            )
        return confirmed
