from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from core.enums import UserRole
from exception.ride_exceptions import raise_ride_http_exception
from schemas.rides.history import RideHistoryItem, RideHistoryResponse
from services.rides import RideHistoryService

from .dependencies import get_current_user_id, get_current_user_role, get_ride_history_service

router = APIRouter()


@router.get(
    "/history",
    response_model=RideHistoryResponse,
    summary="Get paginated ride history for the current user",
)
async def get_ride_history(
    user_id: UUID = Depends(get_current_user_id),
    role: UserRole = Depends(get_current_user_role),
    service: RideHistoryService = Depends(get_ride_history_service),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> RideHistoryResponse:
    try:
        rides, total = await service.get_history(user_id, role, page=page, page_size=page_size)
        items = [RideHistoryItem.model_validate(r) for r in rides]
        return RideHistoryResponse(rides=items, total=total, page=page, page_size=page_size)
    except Exception as exc:
        raise_ride_http_exception(exc)
