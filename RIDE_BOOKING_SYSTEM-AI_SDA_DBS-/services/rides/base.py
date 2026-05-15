from __future__ import annotations

from app.config import Settings
from repositories.ride_repository import RideRepository


class RideServiceBase:
    def __init__(self, repository: RideRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings
