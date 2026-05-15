from __future__ import annotations

from fastapi import APIRouter

from api.endpoints.admin import router as admin_router
from api.endpoints.auth import router as auth_router
from api.endpoints.matching import router as matching_router
from api.endpoints.rides import router as rides_router
from api.endpoints.payments import router as payments_router
from api.endpoints.driver import router as driver_router
from api.endpoints.integrations import router as integrations_router

api_router = APIRouter()
api_router.include_router(rides_router)
api_router.include_router(matching_router)
api_router.include_router(auth_router)
api_router.include_router(payments_router)
api_router.include_router(driver_router)
api_router.include_router(admin_router)
api_router.include_router(integrations_router)
