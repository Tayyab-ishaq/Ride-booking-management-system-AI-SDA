from __future__ import annotations

import json
from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import WebSocket


class WebSocketHub:
    """In-memory websocket connection registry for rider/driver channels."""

    def __init__(self) -> None:
        self._rider_sockets: dict[UUID, set[WebSocket]] = defaultdict(set)
        self._driver_sockets: dict[UUID, set[WebSocket]] = defaultdict(set)

    async def connect_rider(self, user_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rider_sockets[user_id].add(websocket)

    async def connect_driver(self, driver_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._driver_sockets[driver_id].add(websocket)

    def disconnect_rider(self, user_id: UUID, websocket: WebSocket) -> None:
        sockets = self._rider_sockets.get(user_id)
        if sockets is None:
            return
        sockets.discard(websocket)
        if not sockets:
            self._rider_sockets.pop(user_id, None)

    def disconnect_driver(self, driver_id: UUID, websocket: WebSocket) -> None:
        sockets = self._driver_sockets.get(driver_id)
        if sockets is None:
            return
        sockets.discard(websocket)
        if not sockets:
            self._driver_sockets.pop(driver_id, None)

    async def emit_to_rider(self, user_id: UUID, event_type: str, data: Any) -> None:
        await self._emit(self._rider_sockets.get(user_id, set()), event_type, data)

    async def emit_to_driver(self, driver_id: UUID, event_type: str, data: Any) -> None:
        await self._emit(self._driver_sockets.get(driver_id, set()), event_type, data)

    async def _emit(self, sockets: set[WebSocket], event_type: str, data: Any) -> None:
        if not sockets:
            return
        payload = json.dumps({"type": event_type, "data": data}, default=str)
        stale: list[WebSocket] = []
        for socket in sockets:
            try:
                await socket.send_text(payload)
            except Exception:
                stale.append(socket)
        for socket in stale:
            sockets.discard(socket)


ws_hub = WebSocketHub()
