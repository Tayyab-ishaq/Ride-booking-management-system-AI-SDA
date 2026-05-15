from __future__ import annotations

from typing import AsyncIterator

import asyncpg
from fastapi import Request, WebSocket


async def get_db(request: Request) -> AsyncIterator[asyncpg.Connection]:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise RuntimeError("Database pool is not initialized")

    async with pool.acquire() as connection:
        yield connection


async def get_db_ws(websocket: WebSocket) -> AsyncIterator[asyncpg.Connection]:
    pool = getattr(websocket.app.state, "db_pool", None)
    if pool is None:
        raise RuntimeError("Database pool is not initialized")

    async with pool.acquire() as connection:
        yield connection
