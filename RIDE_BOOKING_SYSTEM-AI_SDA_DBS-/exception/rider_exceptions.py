from __future__ import annotations

from fastapi import HTTPException, status


class RiderError(Exception):
    pass


class RiderExists(RiderError):
    pass


class RiderNotFound(RiderError):
    pass


class RiderRepositoryError(RiderError):
    pass


class RiderDatabaseSchemaError(RiderRepositoryError):
    pass


def raise_rider_http_exception(exc: Exception) -> None:
    if isinstance(exc, RiderExists):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, RiderNotFound):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, RiderDatabaseSchemaError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    if isinstance(exc, RiderRepositoryError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected rider error",
    ) from exc
