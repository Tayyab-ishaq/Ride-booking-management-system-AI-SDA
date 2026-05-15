from __future__ import annotations

from typing import Any

import asyncpg


async def create_pool(
    database_url: str,
    min_size: int = 1,
    max_size: int = 10,
) -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=database_url,
        min_size=min_size,
        max_size=max_size,
    )


async def close_pool(pool: asyncpg.Pool | None) -> None:
    if pool is not None:
        await pool.close()

# Important concept

# Without pooling:

# Request -> Create connection -> Query -> Destroy connection

# With pooling:

# Request -> Reuse existing connection -> Query -> Return connection

# That reuse is the main idea behind a database pool.