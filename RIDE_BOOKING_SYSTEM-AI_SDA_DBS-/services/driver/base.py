from __future__ import annotations

from app.config import Settings
from repositories.driver_repository import DriverRepository


class DriverServiceBase:
    def __init__(self, repository: DriverRepository, settings: Settings):
        self.repository = repository
        self.settings = settings
