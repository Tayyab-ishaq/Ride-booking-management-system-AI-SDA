from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from core.ws import ws_hub
from exception.payment_exceptions import raise_payment_http_exception
from schemas.payments.confirm import (
    ConfirmPaymentByPathRequest,
    ConfirmPaymentRequest,
    ConfirmPaymentResponse,
)
from services.integrations import N8NWebhookService
from services.payments.confirm import PaymentConfirmService

from .dependencies import (
    get_current_user_id,
    get_n8n_webhook_service,
    get_payment_confirm_service,
)

router = APIRouter()


def _build_payment_event_payload(payment) -> dict:
    return {
        "ride_id": str(payment.ride_id),
        "payment_id": str(payment.id),
        "user_id": str(payment.user_id),
        "amount": float(payment.amount),
        "status": payment.status.value,
        "timestamp": payment.updated_at.isoformat(),
    }


@router.post(
    "/confirm",
    response_model=ConfirmPaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm a payment",
)
async def confirm_payment(
    payload: ConfirmPaymentRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: PaymentConfirmService = Depends(get_payment_confirm_service),
    n8n_service: N8NWebhookService = Depends(get_n8n_webhook_service),
) -> ConfirmPaymentResponse:
    try:
        payment = await service.confirm_payment(
            payment_id=payload.payment_id,
            user_id=user_id,
            transaction_id=payload.transaction_id,
        )
        await ws_hub.emit_to_rider(
            payment.user_id,
            "payment_done",
            {
                "payment_id": str(payment.id),
                "ride_id": str(payment.ride_id),
                "status": payment.status.value,
                "amount": str(payment.amount),
            },
        )

        await n8n_service.send_event(
            "payment_completed",
            _build_payment_event_payload(payment),
        )

        return ConfirmPaymentResponse.model_validate(payment)
    except Exception as exc:
        raise_payment_http_exception(exc)


@router.post(
    "/{payment_id}/confirm",
    response_model=ConfirmPaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm a payment with transaction ID (legacy path)",
)
async def confirm_payment_legacy(
    payment_id: UUID,
    payload: ConfirmPaymentByPathRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: PaymentConfirmService = Depends(get_payment_confirm_service),
    n8n_service: N8NWebhookService = Depends(get_n8n_webhook_service),
) -> ConfirmPaymentResponse:
    try:
        payment = await service.confirm_payment(
            payment_id=payment_id,
            user_id=user_id,
            transaction_id=payload.transaction_id,
        )
        await ws_hub.emit_to_rider(
            payment.user_id,
            "payment_done",
            {
                "payment_id": str(payment.id),
                "ride_id": str(payment.ride_id),
                "status": payment.status.value,
                "amount": str(payment.amount),
            },
        )

        await n8n_service.send_event(
            "payment_completed",
            _build_payment_event_payload(payment),
        )

        return ConfirmPaymentResponse.model_validate(payment)
    except Exception as exc:
        raise_payment_http_exception(exc)
