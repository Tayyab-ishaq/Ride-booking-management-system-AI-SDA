from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from exception.payment_exceptions import raise_payment_http_exception
from schemas.payments.methods import PaymentMethodRequest, PaymentMethodResponse
from services.payments.methods import PaymentMethodService

from .dependencies import get_current_user_id, get_payment_method_service

router = APIRouter()


@router.get(
    "/methods",
    response_model=list[PaymentMethodResponse],
    status_code=status.HTTP_200_OK,
    summary="List stored payment methods",
)
async def list_payment_methods(
    user_id: UUID = Depends(get_current_user_id),
    service: PaymentMethodService = Depends(get_payment_method_service),
) -> list[PaymentMethodResponse]:
    try:
        methods = await service.list_methods(user_id)
        return [PaymentMethodResponse.model_validate(method) for method in methods]
    except Exception as exc:
        raise_payment_http_exception(exc)


@router.post(
    "/methods",
    response_model=PaymentMethodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new payment method",
)
async def add_payment_method(
    payload: PaymentMethodRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: PaymentMethodService = Depends(get_payment_method_service),
) -> PaymentMethodResponse:
    try:
        method = await service.add_method(
            user_id=user_id,
            method_type=payload.method_type,
            token_ref=payload.token,
            is_default=payload.is_default,
        )
        return PaymentMethodResponse.model_validate(method)
    except Exception as exc:
        raise_payment_http_exception(exc)


@router.delete(
    "/methods/{method_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove stored payment method",
)
async def remove_payment_method(
    method_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: PaymentMethodService = Depends(get_payment_method_service),
) -> None:
    try:
        await service.delete_method(user_id=user_id, method_id=method_id)
    except Exception as exc:
        raise_payment_http_exception(exc)
