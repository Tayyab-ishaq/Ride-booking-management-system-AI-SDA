from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.endpoints.rides.dependencies import (
    get_current_driver_id,
    get_n8n_webhook_service,
    get_ride_matching_service,
)
from core.ws import ws_hub
from exception.ride_exceptions import raise_ride_http_exception
from schemas.matching.accept import MatchingAcceptRequest
from schemas.rides.get import RideDetailResponse
from services.integrations import N8NWebhookService
from services.rides.matching import RideMatchingService

router = APIRouter()


@router.post(
    "/accept",
    response_model=RideDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Driver accepts a matched ride offer",
)
async def accept_matched_ride(
    payload: MatchingAcceptRequest,
    driver_id: UUID = Depends(get_current_driver_id),
    service: RideMatchingService = Depends(get_ride_matching_service),
    n8n_service: N8NWebhookService = Depends(get_n8n_webhook_service),
) -> RideDetailResponse:
    try:
        ride = await service.driver_accept_matched_ride(payload.ride_id, driver_id)
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
        await ws_hub.emit_to_driver(
            driver_id,
            "status_update",
            event_payload,
        )
        await n8n_service.send_event("ride_accepted", event_payload)
        return RideDetailResponse.model_validate(ride)
    except Exception as exc:
        raise_ride_http_exception(exc)
