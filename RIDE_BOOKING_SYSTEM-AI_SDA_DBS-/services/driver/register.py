from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from core.enums import UserRole
from core.security import hash_password
from exception.driver_exceptions import DriverExists
from models.driver import Driver
from repositories.driver_repository import DriverRepository
from schemas.driver.register import DriverRegisterRequest
from repositories.auth_repository import AuthRepository
from models.user import User

from .base import DriverServiceBase


class RegisterDriverService(DriverServiceBase):
    async def register_driver(self, payload: DriverRegisterRequest) -> Driver:
        # Use AuthRepository when running against a real DB connection,
        # otherwise fall back to injected repository (used by unit tests).
        if hasattr(self.repository, "connection"):
            auth_repo = AuthRepository(self.repository.connection)
        else:
            auth_repo = self.repository

        existing_user = await auth_repo.get_by_email(payload.email)
        if existing_user is not None:
            raise DriverExists("Driver with this email already exists")

        # Create the base user, driver, and vehicle rows in a single transaction
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid4(),
            full_name=payload.full_name,
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            role=UserRole.driver,
            created_at=now,
            updated_at=now,
        )

        if hasattr(self.repository, "connection") and hasattr(self.repository.connection, "transaction"):
            async with self.repository.connection.transaction():
                created_user = await auth_repo.create(user)

                # Build Driver object linked to the created user (use same id)
                driver = Driver(
                    id=created_user.id,
                    full_name=created_user.full_name,
                    email=created_user.email,
                    password_hash=created_user.password_hash,
                    role=created_user.role,
                    created_at=created_user.created_at,
                    updated_at=created_user.updated_at,
                    license_number=payload.license_number,
                    vehicle_number=payload.vehicle_number,
                    vehicle_type=payload.vehicle_type,
                    rating=Decimal('0.00'),
                    total_rides=0,
                    is_available=True,
                )
                created_driver = await self.repository.create(driver)

                # If repository supports creating a vehicle record (real DB), persist vehicle details
                make_model = getattr(payload, "vehicle_make_model", None)
                color = getattr(payload, "vehicle_color", None)
                if hasattr(self.repository, "create_vehicle") and make_model:
                    await self.repository.create_vehicle(
                        created_driver.id,
                        payload.vehicle_number,
                        make_model,
                        color,
                        payload.vehicle_type,
                    )
        else:
            created_user = await auth_repo.create(user)

            driver = Driver(
                id=created_user.id,
                full_name=created_user.full_name,
                email=created_user.email,
                password_hash=created_user.password_hash,
                role=created_user.role,
                created_at=created_user.created_at,
                updated_at=created_user.updated_at,
                license_number=payload.license_number,
                vehicle_number=payload.vehicle_number,
                vehicle_type=payload.vehicle_type,
                rating=Decimal('0.00'),
                total_rides=0,
                is_available=True,
            )
            created_driver = await self.repository.create(driver)

            make_model = getattr(payload, "vehicle_make_model", None)
            color = getattr(payload, "vehicle_color", None)
            if hasattr(self.repository, "create_vehicle") and make_model:
                await self.repository.create_vehicle(
                    created_driver.id,
                    payload.vehicle_number,
                    make_model,
                    color,
                    payload.vehicle_type,
                )

        return Driver(
            id=created_user.id,
            full_name=created_user.full_name,
            email=created_user.email,
            password_hash=created_user.password_hash,
            role=created_user.role,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at,
            license_number=payload.license_number,
            vehicle_number=payload.vehicle_number,
            vehicle_type=payload.vehicle_type,
            rating=Decimal('0.00'),
            total_rides=0,
            is_available=True,
        )
