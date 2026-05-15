from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, status

from exception.payment_exceptions import raise_payment_http_exception
from schemas.payments.initiate import PaymentInitiateRequest, PaymentInitiateResponse
from services.payments import PaymentCreateService

from .dependencies import get_current_user_id, get_payment_create_service

router = APIRouter()


@router.post(
    "/initiate",
    response_model=PaymentInitiateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a payment for a completed ride",
)
async def initiate_payment(
    payload: PaymentInitiateRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: PaymentCreateService = Depends(get_payment_create_service),
) -> PaymentInitiateResponse:
    try:
        payment = await service.create_payment(
            ride_id=payload.ride_id,
            user_id=user_id,
            amount=payload.amount,
            payment_method=payload.payment_method,
        )
        return PaymentInitiateResponse.model_validate(payment)
    except Exception as exc:
        raise_payment_http_exception(exc)