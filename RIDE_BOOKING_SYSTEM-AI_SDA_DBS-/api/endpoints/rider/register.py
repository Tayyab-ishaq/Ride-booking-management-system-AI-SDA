from __future__ import annotations

from fastapi import APIRouter, Depends, status

from schemas.rider.register import RiderRegisterRequest, RiderResponse
from services.rider import RegisterRiderService
from exception.rider_exceptions import raise_rider_http_exception

from .dependencies import get_register_rider_service

router = APIRouter()


@router.post("/rider/register", response_model=RiderResponse, status_code=status.HTTP_201_CREATED)
async def register_rider(
    payload: RiderRegisterRequest,
    service: RegisterRiderService = Depends(get_register_rider_service),
) -> RiderResponse:
    try:
        rider = await service.register_rider(payload)
    except Exception as exc:
        raise_rider_http_exception(exc)
    return RiderResponse.model_validate(rider)
