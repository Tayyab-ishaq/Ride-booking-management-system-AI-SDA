from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.endpoints.rides.dependencies import (
    get_current_rider_id,
    get_ride_matching_service,
)
from exception.ride_exceptions import raise_ride_http_exception
from schemas.matching.status import MatchingStatusResponse
from services.rides.matching import RideMatchingService

router = APIRouter()


@router.get(
    "/status/{ride_id}",
    response_model=MatchingStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Poll match progress for a ride",
    description="Get current status of driver matching for a ride request. Can be polled by rider to check if a driver has been matched.",
)
async def get_matching_status(
    ride_id: UUID,
    rider_id: UUID = Depends(get_current_rider_id),
    service: RideMatchingService = Depends(get_ride_matching_service),
) -> MatchingStatusResponse:
    """
    Poll endpoint to check match progress.
    
    Returns current ride status including:
    - status: Current ride state (requested, accepted, in_progress, completed, cancelled)
    - driver_id: Assigned driver ID if matched (None if still searching)
    - fare: Calculated fare if matched
    
    Client should poll this endpoint until status changes from 'requested' or until timeout.
    """
    try:
        ride = await service.get_matching_status(ride_id, rider_id)
        return MatchingStatusResponse.model_validate(ride)
    except Exception as exc:
        raise_ride_http_exception(exc)
