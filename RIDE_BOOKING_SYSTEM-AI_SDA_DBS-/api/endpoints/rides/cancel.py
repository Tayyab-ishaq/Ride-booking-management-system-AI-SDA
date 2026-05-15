from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from core.ws import ws_hub
from exception.ride_exceptions import raise_ride_http_exception
from schemas.rides.status import RideStatusResponse
from services.rides import RideLifecycleService

from .dependencies import get_current_user_id, get_ride_lifecycle_service

router = APIRouter()


@router.post(
    "/{ride_id}/cancel",
    response_model=RideStatusResponse,
    summary="Cancel a ride (rider or driver)",
)
async def cancel_ride(
    ride_id: UUID,
    _user_id: UUID = Depends(get_current_user_id),
    service: RideLifecycleService = Depends(get_ride_lifecycle_service),
) -> RideStatusResponse:
    try:
        ride = await service.cancel_ride(ride_id)
        payload = {"ride_id": str(ride.id), "status": ride.status.value}
        await ws_hub.emit_to_rider(ride.rider_id, "ride_cancelled", payload)
        if ride.driver_id is not None:
            await ws_hub.emit_to_driver(ride.driver_id, "ride_cancelled", payload)
        return RideStatusResponse.model_validate(ride)
    except Exception as exc:
        raise_ride_http_exception(exc)
