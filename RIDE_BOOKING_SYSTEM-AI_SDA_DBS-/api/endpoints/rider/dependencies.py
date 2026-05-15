from __future__ import annotations

from fastapi import Depends

from app.config import Settings, get_settings
from app.dependencies import get_db
from repositories.rider_repository import RiderRepository
from services.rider import RegisterRiderService


def get_register_rider_service(
    connection=Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RegisterRiderService:
    return RegisterRiderService(RiderRepository(connection), settings)
