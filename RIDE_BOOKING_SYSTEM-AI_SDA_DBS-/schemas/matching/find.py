from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class MatchingFindRequest(BaseModel):
    ride_id: UUID
