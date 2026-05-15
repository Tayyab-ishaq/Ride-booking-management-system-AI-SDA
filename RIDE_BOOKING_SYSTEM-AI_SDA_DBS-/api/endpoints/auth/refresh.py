from __future__ import annotations

from fastapi import APIRouter, Depends

from exception.auth_exceptions import raise_auth_http_exception
from schemas.auth.session import RefreshTokenRequest, TokenPairResponse
from services.auth import SessionAuthService

from .dependencies import get_session_auth_service

router = APIRouter()


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    service: SessionAuthService = Depends(get_session_auth_service),
) -> TokenPairResponse:
    try:
        return await service.refresh_access_token(payload.refresh_token)
    except Exception as exc:
        raise_auth_http_exception(exc)
