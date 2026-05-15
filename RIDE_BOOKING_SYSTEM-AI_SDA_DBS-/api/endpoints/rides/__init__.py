from __future__ import annotations

from fastapi import APIRouter

from .cancel import router as cancel_router
from .create import router as create_router
from .get import router as get_router
from .history import router as history_router
from .rate_driver import router as rate_driver_router
from .status import router as status_router

# history MUST be registered before /{ride_id} — FastAPI matches in order,
# and "history" would otherwise be swallowed as a UUID path parameter.
router = APIRouter(prefix="/rides", tags=["rides"])
router.include_router(history_router)
router.include_router(create_router)
router.include_router(get_router)
router.include_router(cancel_router)
router.include_router(status_router)
router.include_router(rate_driver_router)
