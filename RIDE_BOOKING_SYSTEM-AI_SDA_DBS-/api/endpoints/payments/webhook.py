from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from exception.payment_exceptions import PaymentWebhookError, raise_payment_http_exception
from services.payments.webhook import PaymentWebhookService

from .dependencies import get_payment_webhook_service

router = APIRouter()


@router.post(
    "/webhook/payment-gateway",
    status_code=status.HTTP_200_OK,
    summary="Handle payment gateway webhook",
)
async def handle_payment_webhook(
    request: Request,
    service: PaymentWebhookService = Depends(get_payment_webhook_service),
):
    try:
        payload_bytes = await request.body()
        payload = payload_bytes.decode("utf-8")
        signature = request.headers.get("X-Signature")
        if not await service.verify_webhook_signature(payload, signature):
            raise PaymentWebhookError("Invalid webhook signature")

        webhook_data = await request.json()
        updated_payment = await service.handle_payment_webhook(webhook_data)
        return {"status": "success", "payment_id": str(updated_payment.id)}
    except Exception as exc:
        raise_payment_http_exception(exc)
