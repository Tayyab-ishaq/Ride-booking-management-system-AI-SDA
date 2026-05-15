from __future__ import annotations

import hashlib
import hmac
from uuid import UUID

from exception.payment_exceptions import PaymentWebhookError, PaymentNotFound
from services.payments.base import PaymentServiceBase


class PaymentWebhookService(PaymentServiceBase):
    """Service for handling payment gateway webhooks"""

    async def handle_payment_webhook(self, webhook_data: dict):
        """Handle incoming webhook from payment gateway"""
        try:
            transaction_id = webhook_data.get("transaction_id")
            status = webhook_data.get("status")
            
            if not transaction_id or not status:
                raise PaymentWebhookError("Missing required webhook fields")
            
            # Get payment by transaction ID
            payment = await self.repository.get_payment_by_transaction_id(transaction_id)
            
            # Update payment status based on webhook
            updated_payment = await self.repository.update_payment_status(
                payment.id, status
            )
            
            return updated_payment
        except PaymentNotFound as e:
            raise PaymentWebhookError(f"Payment not found for transaction: {str(e)}")
        except Exception as e:
            raise PaymentWebhookError(f"Webhook processing failed: {str(e)}")

    async def verify_webhook_signature(self, payload: str, signature: str | None) -> bool:
        """Verify webhook signature using HMAC-SHA256 and shared secret."""
        if not signature:
            return False
        expected = hmac.new(
            self.settings.payment_webhook_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature.strip())
