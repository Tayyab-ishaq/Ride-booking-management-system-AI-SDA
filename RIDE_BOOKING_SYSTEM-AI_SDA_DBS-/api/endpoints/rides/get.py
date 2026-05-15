from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from exception.ride_exceptions import raise_ride_http_exception
from schemas.rides.get import RideDetailResponse
from services.rides import RideLifecycleService

from .dependencies import get_current_user_id, get_ride_lifecycle_service

router = APIRouter()


@router.get(
    "/{ride_id}",
    response_model=RideDetailResponse,
    summary="Get ride details by ID",
)
async def get_ride(
    ride_id: UUID,
    _user_id: UUID = Depends(get_current_user_id),
    service: RideLifecycleService = Depends(get_ride_lifecycle_service),
) -> RideDetailResponse:
    try:
        ride = await service.get_ride(ride_id)
        return RideDetailResponse.model_validate(ride)
    except Exception as exc:
        raise_ride_http_exception(exc)
