from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from api.router import api_router
from api.endpoints.websocket import router as websocket_router
from db.connection import close_pool, create_pool

API_PREFIX = "/api"


@asynccontextmanager
async def lifespan(app: FastAPI): # It handles both startup + cleanup in one place.
    settings = get_settings() # Load config (DB URL, pool sizes, etc.)

    # Request → Open DB connection → Query → Close connection ❌
    # instead of opening db connection on every request we create a pool which return the database if it connected already
    # you can see the example flow of pool, below the code
    pool = await create_pool(
        database_url=settings.database_url,
        min_size=settings.db_pool_min_size, # minimum number of connections always ready
        max_size=settings.db_pool_max_size, # maximum number of connections always ready
    )
    # Store shared resources in app.state
    app.state.db_pool = pool # Pool accessible anywhere in your app:
    app.state.settings = settings # Settings accessible anywhere in your app:
    try:
        yield # This is where FastAPI starts handling requests.
    finally:
        await close_pool(pool) # Closes all DB connections properly


app = FastAPI(title="Ride Booking Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Routing:
# When a request comes in → FastAPI checks the path → finds the matching route → runs the corresponding function.
app.include_router(api_router, prefix=API_PREFIX)
app.include_router(websocket_router)

# Purpose of main.py
# The app starts in main.py, loads settings, opens a PostgreSQL pool with asyncpg, 
# and stores that pool on app state.


# 📊 Example flow of pool

# Let’s say:

# min_size = 2
# max_size = 10
# At startup:
# 2 connections are created
# When traffic increases:
# Pool grows up to 10 connections
# If all connections are busy:
# New requests wait until one is free
