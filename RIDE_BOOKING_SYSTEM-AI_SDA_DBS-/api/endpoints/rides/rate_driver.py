from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from exception.ride_exceptions import raise_ride_http_exception
from schemas.rides.rating import RateDriverRequest, RatingResponse
from services.rides import DriverRatingService

from .dependencies import get_current_rider_id, get_driver_rating_service

router = APIRouter()


@router.post(
    "/{ride_id}/rating",
    response_model=RatingResponse,
    summary="Rider rates the driver after a completed ride",
)
async def rate_driver(
    ride_id: UUID,
    payload: RateDriverRequest,
    rider_id: UUID = Depends(get_current_rider_id),
    service: DriverRatingService = Depends(get_driver_rating_service),
) -> RatingResponse:
    try:
        ride = await service.rate_driver(ride_id, payload, rider_id)
        return RatingResponse.model_validate(ride)
    except Exception as exc:
        raise_ride_http_exception(exc)
