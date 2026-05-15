from __future__ import annotations

from fastapi import APIRouter, Depends
from uuid import UUID

from app.dependencies import get_db
from app.config import get_settings
from repositories.ride_repository import RideRepository
from core.security import decode_refresh_token

from exception.auth_exceptions import raise_auth_http_exception
from schemas.auth.session import LogoutRequest, MessageResponse
from services.auth import SessionAuthService

from .dependencies import get_session_auth_service

router = APIRouter()


@router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: LogoutRequest,
    service: SessionAuthService = Depends(get_session_auth_service),
    connection=Depends(get_db),
) -> MessageResponse:
    try:
        # Attempt to decode refresh token to identify user and archive any active ride
        settings = get_settings()
        try:
            decoded = decode_refresh_token(
                payload.refresh_token, settings.jwt_secret, settings.jwt_algorithm
            )
            sub = decoded.get("sub")
            if sub:
                rider_id = UUID(sub)
                ride_repo = RideRepository(connection)
                active = await ride_repo.get_active_ride_by_rider(rider_id)
                if active is not None:
                    await ride_repo.archive_and_delete(active.id)
        except Exception:
            # If token decode fails, proceed to revoke token as usual
            pass

        await service.logout(payload.refresh_token)
        return MessageResponse(message="Logout successful")
    except Exception as exc:
        raise_auth_http_exception(exc)
