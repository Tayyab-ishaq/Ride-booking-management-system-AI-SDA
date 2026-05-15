from __future__ import annotations

from fastapi import APIRouter, Depends, status

from schemas.driver.register import DriverRegisterRequest, DriverResponse
from services.driver import RegisterDriverService
from exception.driver_exceptions import raise_driver_http_exception

from .dependencies import get_register_driver_service
from .discovery import router as discovery_router
from .location import router as location_router
from .request import router as request_router

router = APIRouter()
router.include_router(location_router)
router.include_router(request_router)
router.include_router(discovery_router)


@router.post("/driver/register", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def register_driver(
    payload: DriverRegisterRequest,
    service: RegisterDriverService = Depends(get_register_driver_service),
) -> DriverResponse:
    try:
        driver = await service.register_driver(payload)
    except Exception as exc:
        raise_driver_http_exception(exc)
    return DriverResponse.model_validate(driver)
