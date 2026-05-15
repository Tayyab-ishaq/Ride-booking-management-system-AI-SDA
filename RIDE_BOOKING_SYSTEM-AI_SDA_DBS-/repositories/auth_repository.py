from __future__ import annotations
from uuid import UUID
import asyncpg

from db.queries.auth_queries import INSERT_RIDER_PROFILE_IF_MISSING, INSERT_USER, SELECT_USER_BY_EMAIL
from exception.auth_exceptions import AuthDatabaseSchemaError, AuthRepositoryError, UserExists
from models.user import User
from db.queries.auth_queries import INSERT_USER, SELECT_USER_BY_EMAIL, SELECT_USER_BY_ID


class AuthRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection

    async def get_by_id(self, user_id: UUID) -> User | None:
        try:
            record = await self.connection.fetchrow(SELECT_USER_BY_ID, user_id)
        except asyncpg.UndefinedTableError as exc:
            raise AuthDatabaseSchemaError("Users table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise AuthRepositoryError("Failed to read user from database") from exc
        if record is None:
            return None
        return User.from_record(record)
    
    async def get_by_email(self, email: str) -> User | None:
        try:
            record = await self.connection.fetchrow(SELECT_USER_BY_EMAIL, email.lower())
        except asyncpg.UndefinedTableError as exc:
            raise AuthDatabaseSchemaError("Users table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise AuthRepositoryError("Failed to read user from database") from exc
        if record is None:
            return None
        return User.from_record(record)

    async def create(self, user: User) -> User:
        try:
            record = await self.connection.fetchrow(
                INSERT_USER,
                user.id,
                user.full_name,
                user.email.lower(),
                user.password_hash,
                user.role.value,
            )
        except asyncpg.UniqueViolationError as exc:
            raise UserExists("User already exists") from exc
        except asyncpg.UndefinedTableError as exc:
            raise AuthDatabaseSchemaError("Users table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise AuthRepositoryError("Failed to create user in database") from exc
        if record is None:
            raise AuthRepositoryError("Failed to create user in database")
        return User.from_record(record)

    async def create_rider_profile_if_missing(self, user_id: UUID) -> None:
        try:
            await self.connection.execute(INSERT_RIDER_PROFILE_IF_MISSING, user_id)
        except asyncpg.UndefinedTableError as exc:
            raise AuthDatabaseSchemaError("Rider profiles table is missing. Run DB migrations first.") from exc
        except asyncpg.PostgresError as exc:
            raise AuthRepositoryError("Failed to create rider profile") from exc
