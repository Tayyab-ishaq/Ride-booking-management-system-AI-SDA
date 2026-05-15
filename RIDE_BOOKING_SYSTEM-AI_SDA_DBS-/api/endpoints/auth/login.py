from __future__ import annotations

from fastapi import APIRouter, Depends

from exception.auth_exceptions import raise_auth_http_exception
from schemas.auth.session import LoginRequest, TokenPairResponse
from services.auth import SessionAuthService

from .dependencies import get_session_auth_service

router = APIRouter()


@router.post("/login", response_model=TokenPairResponse)
async def login_user(
    payload: LoginRequest,
    service: SessionAuthService = Depends(get_session_auth_service),
) -> TokenPairResponse:
    try:
        return await service.login_user(payload)
    except Exception as exc:
        raise_auth_http_exception(exc)



