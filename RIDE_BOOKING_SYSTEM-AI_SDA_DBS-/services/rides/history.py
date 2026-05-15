from __future__ import annotations

from uuid import UUID

from core.enums import UserRole
from models.ride import Ride

from .base import RideServiceBase


class RideHistoryService(RideServiceBase):

    async def get_history(
        self,
        user_id: UUID,
        role: UserRole,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Ride], int]:
        """
        Return paginated rides for the given user.
        Pagination happens in the DB (LIMIT/OFFSET) — not in Python memory.
        Returns (rides_on_this_page, grand_total_count).
        """
        limit = page_size
        offset = (page - 1) * page_size

        if role == UserRole.driver:
            return await self.repository.get_history_by_driver(user_id, limit, offset)
        return await self.repository.get_history_by_rider(user_id, limit, offset)
