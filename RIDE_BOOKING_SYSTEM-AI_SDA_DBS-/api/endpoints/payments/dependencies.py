from __future__ import annotations

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.dependencies import get_db
from core.enums import UserRole
from core.security import decode_access_token
from exception.auth_exceptions import TokenError
from exception.payment_exceptions import raise_payment_http_exception
from repositories.payment_repository import PaymentRepository
from services.integrations import N8NWebhookService
from services.payments import (
    PaymentCreateService,
    PaymentConfirmService,
    PaymentHistoryService,
    PaymentMethodService,
    PaymentRefundService,
    PaymentStatusService,
    PaymentWebhookService,
)

bearer_scheme = HTTPBearer(auto_error=True)


# ------------------------------------------------------------------ #
# Token helpers                                                        #
# ------------------------------------------------------------------ #

def get_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    return credentials.credentials


def _decode_token(token: str, settings: Settings) -> dict:
    return decode_access_token(
        token=token,
        secret_key=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def _extract_uuid(payload: dict) -> UUID:
    sub = payload.get("sub")
    if not sub:
        raise TokenError("Invalid token subject")
    try:
        return UUID(str(sub))
    except ValueError as exc:
        raise TokenError("Token subject is not a valid UUID") from exc


# ------------------------------------------------------------------ #
# Current-user extractors                                              #
# ------------------------------------------------------------------ #

def get_current_user_id(
    token: str = Depends(get_bearer_token),
    settings: Settings = Depends(get_settings),
) -> UUID:
    """Decode the JWT and extract user ID — any authenticated user."""
    try:
        payload = _decode_token(token, settings)
        return _extract_uuid(payload)
    except Exception as exc:
        raise_payment_http_exception(exc)


def get_current_user_role(
    token: str = Depends(get_bearer_token),
    settings: Settings = Depends(get_settings),
) -> UserRole:
    """Decode JWT and extract user role."""
    try:
        payload = _decode_token(token, settings)
        role = payload.get("role")
        if role not in (UserRole.rider.value, UserRole.driver.value):
            raise TokenError("Invalid role in token")
        return UserRole(role)
    except Exception as exc:
        raise_payment_http_exception(exc)


# ------------------------------------------------------------------ #
# Service factories                                                    #
# ------------------------------------------------------------------ #

def get_payment_create_service(
    connection=Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PaymentCreateService:
    return PaymentCreateService(PaymentRepository(connection), settings)


def get_payment_confirm_service(
    connection=Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PaymentConfirmService:
    return PaymentConfirmService(PaymentRepository(connection), settings)


def get_payment_history_service(
    connection=Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PaymentHistoryService:
    return PaymentHistoryService(PaymentRepository(connection), settings)


def get_payment_refund_service(
    connection=Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PaymentRefundService:
    return PaymentRefundService(PaymentRepository(connection), settings)


def get_payment_status_service(
    connection=Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PaymentStatusService:
    return PaymentStatusService(PaymentRepository(connection), settings)


def get_payment_webhook_service(
    connection=Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PaymentWebhookService:
    return PaymentWebhookService(PaymentRepository(connection), settings)


def get_payment_method_service(
    connection=Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PaymentMethodService:
    return PaymentMethodService(PaymentRepository(connection), settings)


def get_n8n_webhook_service(
    settings: Settings = Depends(get_settings),
) -> N8NWebhookService:
    return N8NWebhookService(settings)
