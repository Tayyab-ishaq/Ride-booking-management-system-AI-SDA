from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from api.endpoints.rides.dependencies import get_current_driver_id, get_current_user_id
from app.dependencies import get_db
from exception.driver_exceptions import DriverPermissionError, raise_driver_http_exception
from repositories.driver_repository import DriverRepository

router = APIRouter(prefix="/driver", tags=["driver"])


@router.put(
    "/{driver_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Set driver online/offline/busy",
)
async def set_driver_status(
    driver_id: UUID,
    payload: dict,
    caller_driver_id: UUID = Depends(get_current_driver_id),
    connection=Depends(get_db),
):
    try:
        if str(caller_driver_id) != str(driver_id):
            raise DriverPermissionError("You are not allowed to update another driver")
        status_value = str(payload.get("status", "")).lower()
        is_available = status_value == "online"
        updated = await DriverRepository(connection).update_availability(driver_id, is_available)
        return {"status": status_value, "is_available": updated.is_available if updated else is_available}
    except Exception as exc:
        raise_driver_http_exception(exc)


@router.get(
    "/{driver_id}",
    status_code=status.HTTP_200_OK,
    summary="Get driver by id",
)
async def get_driver_by_id(
    driver_id: UUID,
    _user_id: UUID = Depends(get_current_user_id),
    connection=Depends(get_db),
):
    try:
        driver = await DriverRepository(connection).get_by_id(driver_id)
        return {"driver": driver}
    except Exception as exc:
        raise_driver_http_exception(exc)


@router.get(
    "/nearby",
    status_code=status.HTTP_200_OK,
    summary="List nearby available drivers",
)
async def nearby_drivers(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=5, ge=0.1, le=100),
    _user_id: UUID = Depends(get_current_user_id),
    connection=Depends(get_db),
):
    try:
        drivers = await DriverRepository(connection).get_nearby_drivers(lat, lng, radius_km)
        return {"drivers": drivers, "count": len(drivers)}
    except Exception as exc:
        raise_driver_http_exception(exc)


@router.get(
    "/{driver_id}/earnings",
    status_code=status.HTTP_200_OK,
    summary="Get driver earnings summary",
)
async def driver_earnings(
    driver_id: UUID,
    from_ts: str | None = Query(default=None, alias="from"),
    to_ts: str | None = Query(default=None, alias="to"),
    caller_driver_id: UUID = Depends(get_current_driver_id),
    connection=Depends(get_db),
):
    try:
        # Drivers can only access their own earnings.
        if str(caller_driver_id) != str(driver_id):
            raise DriverPermissionError("You are not allowed to view another driver's earnings")

        return await DriverRepository(connection).get_driver_earnings(
            driver_id=driver_id,
            from_ts=from_ts,
            to_ts=to_ts,
        )
    except Exception as exc:
        raise_driver_http_exception(exc)
