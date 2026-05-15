from __future__ import annotations

from fastapi import HTTPException, status



class AuthError(Exception):
    pass


class InvalidCredentials(AuthError):
    pass


class UserExists(AuthError):
    pass


class TokenError(AuthError):
    pass


class AuthRepositoryError(AuthError):
    pass


class AuthDatabaseSchemaError(AuthRepositoryError):
    pass


def raise_auth_http_exception(exc: Exception) -> None:
    if isinstance(exc, UserExists):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, InvalidCredentials):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if isinstance(exc, TokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if isinstance(exc, AuthDatabaseSchemaError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    if isinstance(exc, AuthRepositoryError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected authentication error",
    ) from exc
