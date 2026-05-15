from __future__ import annotations

from fastapi import APIRouter, Depends

from exception.auth_exceptions import raise_auth_http_exception
from schemas.auth.register import UserResponse
from services.auth import SessionAuthService

from .dependencies import get_bearer_token, get_session_auth_service

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(
    access_token: str = Depends(get_bearer_token),
    service: SessionAuthService = Depends(get_session_auth_service),
) -> UserResponse:
    try:
        user = await service.get_current_user(access_token)
        return UserResponse.model_validate(user)
    except Exception as exc:
        raise_auth_http_exception(exc)
