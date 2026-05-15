from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from core.ws import ws_hub
from exception.ride_exceptions import raise_ride_http_exception
from schemas.rides.status import RideStatusResponse
from services.integrations import N8NWebhookService
from services.rides import RideLifecycleService

from .dependencies import (
    get_current_driver_id,
    get_n8n_webhook_service,
    get_ride_lifecycle_service,
)

router = APIRouter()


@router.patch(
    "/{ride_id}/accept",
    response_model=RideStatusResponse,
    summary="Driver accepts a requested ride",
)
async def accept_ride(
    ride_id: UUID,
    driver_id: UUID = Depends(get_current_driver_id),
    service: RideLifecycleService = Depends(get_ride_lifecycle_service),
    n8n_service: N8NWebhookService = Depends(get_n8n_webhook_service),
) -> RideStatusResponse:
    try:
        ride = await service.accept_ride(ride_id, driver_id)
        event_payload = {
            "ride_id": str(ride.id),
            "driver_id": str(driver_id),
            "rider_id": str(ride.rider_id),
            "status": ride.status.value,
        }
        await ws_hub.emit_to_rider(
            ride.rider_id,
            "ride_accepted",
            event_payload,
        )
        await n8n_service.send_event("ride_accepted", event_payload)
        return RideStatusResponse.model_validate(ride)
    except Exception as exc:
        raise_ride_http_exception(exc)


@router.patch(
    "/{ride_id}/start",
    response_model=RideStatusResponse,
    summary="Driver marks ride as in progress (passenger picked up)",
)
async def start_ride(
    ride_id: UUID,
    driver_id: UUID = Depends(get_current_driver_id),
    service: RideLifecycleService = Depends(get_ride_lifecycle_service),
) -> RideStatusResponse:
    try:
        ride = await service.start_ride(ride_id, driver_id)
        await ws_hub.emit_to_rider(
            ride.rider_id,
            "status_update",
            {"ride_id": str(ride.id), "status": ride.status.value},
        )
        return RideStatusResponse.model_validate(ride)
    except Exception as exc:
        raise_ride_http_exception(exc)


@router.patch(
    "/{ride_id}/complete",
    response_model=RideStatusResponse,
    summary="Driver marks ride as completed (passenger dropped off)",
)
async def complete_ride(
    ride_id: UUID,
    driver_id: UUID = Depends(get_current_driver_id),
    service: RideLifecycleService = Depends(get_ride_lifecycle_service),
    n8n_service: N8NWebhookService = Depends(get_n8n_webhook_service),
) -> RideStatusResponse:
    try:
        ride = await service.complete_ride(ride_id, driver_id)
        payload = {
            "ride_id": str(ride.id),
            "driver_id": str(driver_id),
            "rider_id": str(ride.rider_id),
            "status": ride.status.value,
        }
        await ws_hub.emit_to_rider(ride.rider_id, "ride_completed", payload)
        await ws_hub.emit_to_driver(driver_id, "ride_completed", payload)
        await n8n_service.send_event("ride_completed", payload)
        return RideStatusResponse.model_validate(ride)
    except Exception as exc:
        raise_ride_http_exception(exc)
