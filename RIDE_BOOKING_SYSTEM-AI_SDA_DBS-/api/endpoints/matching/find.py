from __future__ import annotations

from uuid import UUID
import logging

from fastapi import APIRouter, Depends, status

from api.endpoints.rides.dependencies import (
    get_current_rider_id,
    get_ride_matching_service,
)
from core.ws import ws_hub
from exception.ride_exceptions import raise_ride_http_exception
from schemas.matching.find import MatchingFindRequest
from schemas.rides.get import RideDetailResponse
from services.rides.matching import RideMatchingService
from repositories.rider_repository import RiderRepository

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/find",
    response_model=RideDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger driver search for a ride request",
)
async def find_match(
    payload: MatchingFindRequest,
    rider_id: UUID = Depends(get_current_rider_id),
    service: RideMatchingService = Depends(get_ride_matching_service),
) -> RideDetailResponse:
    try:
        logger.info(f"Finding driver for ride: {payload.ride_id}, rider: {rider_id}")
        ride = await service.find_driver_for_ride(payload.ride_id, rider_id)
        logger.info(f"Found driver {ride.driver_id} for ride {ride.id}")
        
        if ride.driver_id is not None:
            await ws_hub.emit_to_rider(
                ride.rider_id,
                "driver_matched",
                {"ride_id": str(ride.id), "driver_id": str(ride.driver_id), "status": ride.status.value},
            )
            
            # Include rider's full name in driver offer payload to avoid extra fetches on the client
            try:
                rider_repo = RiderRepository(service.repository.connection)
                rider = await rider_repo.get_by_id(ride.rider_id)
                rider_full_name = rider.full_name if (rider is not None) else None
                logger.info(f"Rider full name fetched: {rider_full_name}")
            except Exception as rider_error:
                logger.error(f"Failed to fetch rider full name: {rider_error}")
                rider_full_name = None
            
            await ws_hub.emit_to_driver(
                ride.driver_id,
                "ride_offer",
                {
                    "id": str(ride.id),
                    "ride_id": str(ride.id),
                    "driver_id": str(ride.driver_id),
                    "rider_id": str(ride.rider_id),
                    "rider_full_name": rider_full_name,
                    "origin": ride.origin,
                    "destination": ride.destination,
                },
            )
        return RideDetailResponse.model_validate(ride)
    except Exception as exc:
        logger.error(f"Error in find_match: {exc}", exc_info=True)
        raise_ride_http_exception(exc)
