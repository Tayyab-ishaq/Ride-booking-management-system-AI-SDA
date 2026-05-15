"""Endpoint for drivers to save their location."""
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException
from decimal import Decimal
from pydantic import BaseModel, Field

from api.endpoints.rides.dependencies import get_current_driver_id
from app.dependencies import get_db
from repositories.driver_repository import DriverRepository
from exception.driver_exceptions import raise_driver_http_exception, DriverNotFound


router = APIRouter(prefix="/driver", tags=["driver"])


class SaveDriverLocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


@router.post(
    "/save-location",
    status_code=status.HTTP_200_OK,
    summary="Save driver's location",
    description="Store driver's current coordinates (latitude/longitude) in database"
)
async def save_driver_location(
    payload: SaveDriverLocationRequest,
    driver_id: UUID = Depends(get_current_driver_id),
    connection=Depends(get_db),
):
    """
    Save driver's current location coordinates.
    
    JSON Body:
    - latitude: -90 to +90
    - longitude: -180 to +180
    
    Returns: Location record with timestamp
    """
    # Ensure the token subject corresponds to an actual drivers row.
    # Tokens may contain the user's id (users.id) or the driver's id (drivers.id).
    row = await connection.fetchrow(
        """
        SELECT id FROM drivers WHERE id = $1 OR user_id = $1 LIMIT 1
        """,
        str(driver_id),
    )

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found. Register as a driver first.")

    actual_driver_id = row["id"]

    result = await connection.fetchrow("""
        INSERT INTO driver_locations (driver_id, latitude, longitude, recorded_at)
        VALUES ($1, $2, $3, NOW())
        RETURNING 
            loc_id, 
            driver_id, 
            latitude, 
            longitude, 
            recorded_at
        """, str(actual_driver_id), Decimal(str(payload.latitude)), Decimal(str(payload.longitude)))

    return {
        "loc_id": str(result["loc_id"]),
        "driver_id": str(result["driver_id"]),
        "latitude": float(result["latitude"]),
        "longitude": float(result["longitude"]),
        "recorded_at": result["recorded_at"].isoformat(),
        "message": "✅ Location saved successfully"
    }



class SetDriverStatusRequest(BaseModel):
    is_available: bool


@router.post(
    "/set-status",
    status_code=status.HTTP_200_OK,
    summary="Set driver's availability status",
    description="Set driver online/offline. When set to offline, clears last known locations."
)
async def set_driver_status(
    payload: SetDriverStatusRequest,
    driver_id: UUID = Depends(get_current_driver_id),
    connection=Depends(get_db),
):
    try:
        repo = DriverRepository(connection)
        updated = await repo.update_availability(driver_id, payload.is_available)
        if updated is None:
            raise DriverNotFound("Driver not found")

        if not payload.is_available:
            # Remove stored locations when going offline
            await connection.execute("DELETE FROM driver_locations WHERE driver_id = $1", str(updated.id))

        return {"message": "Status updated", "is_available": updated.is_available}
    except Exception as exc:
        raise_driver_http_exception(exc)



@router.patch(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Set driver's availability status (REST)",
    description="Set driver online/offline. Use DELETE /api/driver/locations to clear locations when offline."
)
async def patch_driver_status(
    payload: SetDriverStatusRequest,
    driver_id: UUID = Depends(get_current_driver_id),
    connection=Depends(get_db),
):
    try:
        repo = DriverRepository(connection)
        updated = await repo.update_availability(driver_id, payload.is_available)
        if updated is None:
            raise DriverNotFound("Driver not found")

        return {"message": "Status updated", "is_available": updated.is_available}
    except Exception as exc:
        raise_driver_http_exception(exc)


@router.delete(
    "/locations",
    status_code=status.HTTP_200_OK,
    summary="Delete driver's stored locations",
    description="Deletes all stored location rows for the authenticated driver."
)
async def delete_driver_locations(
    driver_id: UUID = Depends(get_current_driver_id),
    connection=Depends(get_db),
):
    # Resolve token subject to an actual drivers row (same logic as other handlers)
    row = await connection.fetchrow(
        """
        SELECT id FROM drivers WHERE id = $1 OR user_id = $1 LIMIT 1
        """,
        str(driver_id),
    )

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found. Register as a driver first.")

    actual_driver_id = row["id"]

    await connection.execute("DELETE FROM driver_locations WHERE driver_id = $1", str(actual_driver_id))
    return {"message": "Driver locations deleted"}
