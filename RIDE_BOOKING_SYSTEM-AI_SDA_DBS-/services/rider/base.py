from __future__ import annotations

from app.config import Settings
from repositories.rider_repository import RiderRepository


class RiderServiceBase:
    def __init__(self, repository: RiderRepository, settings: Settings):
        self.repository = repository
        self.settings = settings
