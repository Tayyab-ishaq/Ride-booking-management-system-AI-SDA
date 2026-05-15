from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class MatchingAcceptRequest(BaseModel):
    ride_id: UUID
