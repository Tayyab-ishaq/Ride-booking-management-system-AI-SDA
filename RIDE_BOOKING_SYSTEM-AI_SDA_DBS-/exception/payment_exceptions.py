from __future__ import annotations

from fastapi import HTTPException, status


class PaymentError(Exception):
    pass


class InvalidPaymentMethod(PaymentError):
    pass


class InvalidPaymentStatus(PaymentError):
    pass


class PaymentAlreadyProcessed(PaymentError):
    pass


class PaymentNotFound(PaymentError):
    pass


class PaymentOwnershipError(PaymentError):
    pass


class PaymentWebhookError(PaymentError):
    pass


class PaymentRepositoryError(PaymentError):
    pass


class PaymentDatabaseSchemaError(PaymentRepositoryError):
    pass


class PaymentMethodError(PaymentError):
    pass


class PaymentMethodNotFound(PaymentError):
    pass


def raise_payment_http_exception(exc: Exception) -> None:
    if isinstance(exc, InvalidPaymentMethod):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if isinstance(exc, InvalidPaymentStatus):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if isinstance(exc, PaymentAlreadyProcessed):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, PaymentNotFound):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, PaymentOwnershipError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if isinstance(exc, PaymentWebhookError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if isinstance(exc, PaymentDatabaseSchemaError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    if isinstance(exc, PaymentRepositoryError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected payment error",
    ) from exc