from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.hash import pbkdf2_sha256

from exception.auth_exceptions import TokenError


def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pbkdf2_sha256.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str,
    expires_delta_minutes: int,
) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes)
    payload.update({"exp": expire, "token_type": "access"})
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_refresh_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str,
    expires_delta_minutes: int,
) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes)
    payload.update({"exp": expire, "token_type": "refresh"})
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(token: str, secret_key: str, algorithm: str) -> dict[str, Any]:
    try:
        decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid token") from exc

    if decoded.get("token_type") != "access":
        raise TokenError("Invalid token type")

    return decoded


def decode_refresh_token(token: str, secret_key: str, algorithm: str) -> dict[str, Any]:
    try:
        decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid token") from exc

    if decoded.get("token_type") != "refresh":
        raise TokenError("Invalid token type")

    return decoded
