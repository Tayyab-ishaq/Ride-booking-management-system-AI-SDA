from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.endpoints.rides.dependencies import get_current_driver_id
from app.dependencies import get_db
from exception.ride_exceptions import raise_ride_http_exception
from repositories.ride_repository import RideRepository
from schemas.rides.get import RideDetailResponse

router = APIRouter(prefix="/driver", tags=["driver"])


@router.get(
    "/active-request",
    status_code=status.HTTP_200_OK,
    summary="Get the driver's current assigned ride",
)
async def get_active_request(
    driver_id: UUID = Depends(get_current_driver_id),
    connection=Depends(get_db),
):
    try:
        driver_row = await connection.fetchrow(
            """
            SELECT id FROM drivers WHERE id = $1 OR user_id = $1 LIMIT 1
            """,
            str(driver_id),
        )

        if driver_row is None:
            return {"ride": None}

        actual_driver_id = UUID(str(driver_row["id"]))

        # Query using the canonical drivers.id value. The JWT subject may be users.id.
        ride = await RideRepository(connection).get_active_ride_by_driver(actual_driver_id)
        return {"ride": RideDetailResponse.model_validate(ride) if ride else None}
    except Exception as exc:
        raise_ride_http_exception(exc)
