from __future__ import annotations

from fastapi import APIRouter

from .confirm_payment import router as confirm_payment_router
from .initiate import router as initiate_router
from .methods import router as methods_router
from .webhook import router as webhook_router

router = APIRouter(prefix="/payments", tags=["payments"])
router.include_router(initiate_router)
router.include_router(methods_router)
router.include_router(confirm_payment_router)
router.include_router(webhook_router)