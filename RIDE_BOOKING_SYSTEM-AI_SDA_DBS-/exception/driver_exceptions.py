from __future__ import annotations

from fastapi import HTTPException, status


class DriverError(Exception):
    pass


class DriverExists(DriverError):
    pass


class DriverNotFound(DriverError):
    pass


class DriverPermissionError(DriverError):
    pass


class DriverRepositoryError(DriverError):
    pass


class DriverDatabaseSchemaError(DriverRepositoryError):
    pass


def raise_driver_http_exception(exc: Exception) -> None:
    if isinstance(exc, DriverExists):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, DriverNotFound):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, DriverPermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if isinstance(exc, DriverDatabaseSchemaError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    if isinstance(exc, DriverRepositoryError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected driver error",
    ) from exc
