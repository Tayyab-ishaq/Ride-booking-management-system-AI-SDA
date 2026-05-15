from __future__ import annotations

from fastapi import APIRouter

from .routes import router as routes_router

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(routes_router)
