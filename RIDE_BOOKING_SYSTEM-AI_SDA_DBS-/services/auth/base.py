from __future__ import annotations

from app.config import Settings
from repositories.auth_repository import AuthRepository


class AuthServiceBase:
    def __init__(self, repository: AuthRepository, settings: Settings):
        self.repository = repository
        self.settings = settings
