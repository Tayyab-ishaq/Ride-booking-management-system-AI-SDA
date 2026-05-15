from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from core.security import hash_password
from exception.auth_exceptions import UserExists
from models.user import User
from schemas.auth.register import RegisterRequest
from decimal import Decimal

from core.enums import UserRole
from models.driver import Driver
from repositories.driver_repository import DriverRepository

from .base import AuthServiceBase


class RegisterAuthService(AuthServiceBase):
    async def register_user(self, payload: RegisterRequest) -> User:
        existing_user = await self.repository.get_by_email(payload.email)
        if existing_user is not None:
            raise UserExists("User already exists")

        now = datetime.now(timezone.utc)
        user = User(
            id=uuid4(),
            full_name=payload.full_name,
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            role=payload.role,
            created_at=now,
            updated_at=now,
        )
        # If registering a driver, also create a drivers table row so
        # matching and websocket targeting work for newly-registered drivers.
        if payload.role == UserRole.driver:
            # When running against a real DB connection, perform both inserts
            # in a single transaction to avoid partial state.
            if hasattr(self.repository, "connection") and hasattr(self.repository.connection, "transaction"):
                async with self.repository.connection.transaction():
                    created_user = await self.repository.create(user)
                    driver = Driver(
                        id=created_user.id,
                        full_name=created_user.full_name,
                        email=created_user.email,
                        password_hash=created_user.password_hash,
                        role=created_user.role,
                        created_at=created_user.created_at,
                        updated_at=created_user.updated_at,
                        license_number=None,
                        vehicle_number=None,
                        vehicle_type=None,
                        rating=Decimal('0.00'),
                        total_rides=0,
                        is_available=True,
                    )
                    # Use DriverRepository bound to the same connection
                    driver_repo = DriverRepository(self.repository.connection)
                    await driver_repo.create(driver)
                    return created_user
            # Fallback: create user then driver without explicit transaction
            created_user = await self.repository.create(user)
            driver = Driver(
                id=created_user.id,
                full_name=created_user.full_name,
                email=created_user.email,
                password_hash=created_user.password_hash,
                role=created_user.role,
                created_at=created_user.created_at,
                updated_at=created_user.updated_at,
                license_number=None,
                vehicle_number=None,
                vehicle_type=None,
                rating=Decimal('0.00'),
                total_rides=0,
                is_available=True,
            )
            driver_repo = DriverRepository(self.repository.connection) if hasattr(self.repository, "connection") else DriverRepository(self.repository)
            await driver_repo.create(driver)
            return created_user

        created_user = await self.repository.create(user)
        return created_user
