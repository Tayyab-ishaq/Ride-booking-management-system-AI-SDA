from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.dependencies import get_db
from repositories.auth_repository import AuthRepository
from services.auth import RegisterAuthService, SessionAuthService

bearer_scheme = HTTPBearer(auto_error=True)

# It creates and returns a fully configured RegisterAuthService class object
def get_register_auth_service(
    connection=Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RegisterAuthService:
    return RegisterAuthService(AuthRepository(connection), settings)


def get_session_auth_service(
    connection=Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SessionAuthService:
    return SessionAuthService(AuthRepository(connection), settings)


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    return credentials.credentials
