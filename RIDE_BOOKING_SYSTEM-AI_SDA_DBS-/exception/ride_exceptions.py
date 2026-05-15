from __future__ import annotations

from fastapi import HTTPException, status

from exception.auth_exceptions import TokenError


class RideError(Exception):
    pass


class RideNotFound(RideError):
    pass


class RideAlreadyCancelled(RideError):
    pass


class RideAlreadyRated(RideError):
    pass


class DriverNotAvailable(RideError):
    pass


class RiderHasActiveRide(RideError):
    pass


class RideOwnershipError(RideError):
    pass


class InvalidRideTransition(RideError):
    pass


class RideRepositoryError(RideError):
    pass


class RideDatabaseSchemaError(RideRepositoryError):
    pass


def raise_ride_http_exception(exc: Exception) -> None:
    if isinstance(exc, TokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    if isinstance(exc, RideNotFound):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    if isinstance(exc, RideOwnershipError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    if isinstance(exc, RideAlreadyCancelled):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    if isinstance(exc, RideAlreadyRated):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    if isinstance(exc, DriverNotAvailable):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    if isinstance(exc, RiderHasActiveRide):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    if isinstance(exc, InvalidRideTransition):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    if isinstance(exc, RideDatabaseSchemaError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    if isinstance(exc, RideRepositoryError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected ride error",
    ) from exc
