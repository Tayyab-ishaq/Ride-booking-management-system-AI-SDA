from __future__ import annotations

from fastapi import APIRouter

from .login import router as login_router
from .logout import router as logout_router
from .me import router as me_router
from .refresh import router as refresh_router
from .register import router as register_router

router = APIRouter(prefix="/auth", tags=["auth"])
router.include_router(register_router)
router.include_router(login_router)
router.include_router(refresh_router)
router.include_router(logout_router)
router.include_router(me_router)
