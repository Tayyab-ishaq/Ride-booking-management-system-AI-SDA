from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.dependencies import get_db_ws
from core.ws import ws_hub

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/rider/{user_id}")
async def rider_ws(websocket: WebSocket, user_id: UUID) -> None:
    await ws_hub.connect_rider(user_id, websocket)
    try:
        async for _ in websocket.iter_text():
            # We only keep the socket alive for server-push events.
            # Incoming rider messages are currently ignored.
            pass
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        # Task cancellations can happen during shutdown/reload.
        # Swallow to avoid noisy ASGI tracebacks for expected disconnect paths.
        pass
    except Exception:
        pass
    finally:
        ws_hub.disconnect_rider(user_id, websocket)


@router.websocket("/ws/driver/{driver_id}")
async def driver_ws(
    websocket: WebSocket,
    driver_id: UUID,
    connection=Depends(get_db_ws),
) -> None:
    # Accept driver websocket connections using either the driver row UUID
    # or the associated user UUID for backward compatibility.
    row = await connection.fetchrow(
        "SELECT id FROM drivers WHERE id = $1 OR user_id = $1 LIMIT 1",
        str(driver_id),
    )
    if row is None:
        await websocket.close(code=1008)
        return

    actual_driver_id = UUID(str(row["id"]))
    await ws_hub.connect_driver(actual_driver_id, websocket)
    try:
        async for _ in websocket.iter_text():
            # We only keep the socket alive for server-push events.
            # Incoming driver messages are currently ignored.
            pass
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        # Task cancellations can happen during shutdown/reload.
        # Swallow to avoid noisy ASGI tracebacks for expected disconnect paths.
        pass
    except Exception:
        pass
    finally:
        ws_hub.disconnect_driver(actual_driver_id, websocket)
