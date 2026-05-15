from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.dependencies import get_db
from core.enums import UserRole
from core.security import decode_access_token
from exception.auth_exceptions import TokenError

bearer_scheme = HTTPBearer(auto_error=True)


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    return credentials.credentials


def get_current_admin_id(
    token: str = Depends(get_bearer_token),
    settings: Settings = Depends(get_settings),
) -> UUID:
    try:
        payload = decode_access_token(
            token=token,
            secret_key=settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
        role = payload.get("role")
        if role != UserRole.admin.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can perform this action",
            )
        sub = payload.get("sub")
        if not sub:
            raise TokenError("Invalid token subject")
        return UUID(str(sub))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def get_admin_db(connection=Depends(get_db)):
    return connection
