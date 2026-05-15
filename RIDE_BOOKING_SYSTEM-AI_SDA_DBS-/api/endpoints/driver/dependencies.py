from __future__ import annotations

from fastapi import Depends

from app.config import Settings, get_settings
from app.dependencies import get_db
from repositories.driver_repository import DriverRepository
from services.driver import RegisterDriverService


def get_register_driver_service(
    connection=Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RegisterDriverService:
    return RegisterDriverService(DriverRepository(connection), settings)
