from __future__ import annotations
from uuid import UUID

from core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    verify_password,
)
from exception.auth_exceptions import InvalidCredentials, TokenError
from models.user import User
from schemas.auth.session import LoginRequest, TokenPairResponse

from .base import AuthServiceBase


REVOKED_REFRESH_TOKENS: set[str] = set()


class SessionAuthService(AuthServiceBase):
    async def login_user(self, payload: LoginRequest) -> TokenPairResponse:
        user = await self.repository.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise InvalidCredentials("Invalid email or password")
        return self._build_token_pair(user)

    async def refresh_access_token(self, refresh_token: str) -> TokenPairResponse:
        if refresh_token in REVOKED_REFRESH_TOKENS:
            raise TokenError("Refresh token has been revoked")

        decoded = decode_refresh_token(
            token=refresh_token,
            secret_key=self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
        )
        subject = decoded.get("sub")
        if not isinstance(subject, str) or not subject:
            raise TokenError("Invalid token subject")

        user = await self.repository.get_by_id(UUID(subject)) 
        if user is None:
            raise InvalidCredentials("User not found")

        return self._build_token_pair(user)

    async def get_current_user(self, access_token: str) -> User:
        decoded = decode_access_token(
            token=access_token,
            secret_key=self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
        )
        subject = decoded.get("sub")
        if not isinstance(subject, str) or not subject:
            raise TokenError("Invalid token subject")

        user = await self.repository.get_by_id(UUID(subject)) 
        if user is None:
            raise InvalidCredentials("User not found")
        return user

    async def logout(self, refresh_token: str) -> None:
        decode_refresh_token(
            token=refresh_token,
            secret_key=self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
        )
        REVOKED_REFRESH_TOKENS.add(refresh_token)

    def _build_token_pair(self, user: User) -> TokenPairResponse:
        token_payload = {
            "sub": str(user.id), # this error takes plenty of time, the old line is: user.email
            "role": user.role.value,
        }
        access_token = create_access_token(
            data=token_payload,
            secret_key=self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
            expires_delta_minutes=self.settings.access_token_expire_minutes,
        )
        refresh_token = create_refresh_token(
            data=token_payload,
            secret_key=self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
            expires_delta_minutes=self.settings.refresh_token_expire_minutes,
        )
        return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)
