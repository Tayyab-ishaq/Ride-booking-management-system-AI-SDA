from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status, BackgroundTasks

from schemas.auth.register import RegisterRequest, UserResponse

from .dependencies import get_register_auth_service
from services.auth import RegisterAuthService
from exception.auth_exceptions import raise_auth_http_exception
import httpx

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    service: RegisterAuthService = Depends(get_register_auth_service)
) -> UserResponse:
    try:
        user = await service.register_user(payload)
        background_tasks.add_task(send_registration_webhook, user.email, user.full_name)
    except Exception as exc:
        raise_auth_http_exception(exc)
    return UserResponse.model_validate(user)


async def send_registration_webhook(email: str, full_name: str):
    webhook_url = "http://localhost:5678/webhook/register-success"
    payload = {"email": email, "full_name": full_name}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload, timeout=5.0)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error(
            "Failed to deliver registration webhook to n8n %s: %s",
            webhook_url,
            exc,
        )
    except Exception as exc:
        logger.error(
            "Unexpected error while sending registration webhook to n8n %s: %s",
            webhook_url,
            exc,
        )
