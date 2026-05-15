from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings

router = APIRouter(tags=["integrations"])


@router.get(
    "/integrations/status",
    status_code=status.HTTP_200_OK,
    summary="Integration health snapshot",
)
async def integrations_status():
    now = datetime.now(timezone.utc).isoformat()
    return {
        "timestamp": now,
        "workflows": {
            "driver_ranking": {"status": "configured"},
            "fare_estimate": {"status": "configured"},
            "ride_completed": {"status": "configured"},
        },
    }


@router.post("/webhooks/ride-requested", status_code=status.HTTP_200_OK)
async def webhook_ride_requested(payload: dict):
    return {"accepted": True, "workflow": "ride-requested", "payload": payload}


@router.post("/webhooks/fare-estimate", status_code=status.HTTP_200_OK)
async def webhook_fare_estimate(
    payload: dict,
    settings: Settings = Depends(get_settings),
):
    webhook_url = (
        payload.get("webhook_url")
        or settings.n8n_pricing_webhook_url
        or settings.n8n_webhook_url
    )
    if not webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pricing webhook URL configured.",
        )

    parsed = urlparse(str(webhook_url))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pricing webhook URL.",
        )

    forward_payload = dict(payload)
    forward_payload.pop("webhook_url", None)

    try:
        async with httpx.AsyncClient(timeout=settings.n8n_webhook_timeout_sec) as client:
            response = await client.post(
                str(webhook_url),
                json=forward_payload,
                headers={"Content-Type": "application/json"},
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Pricing webhook request timed out.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Pricing webhook request failed: {exc}",
        ) from exc

    try:
        upstream_data = response.json()
    except ValueError:
        upstream_data = {"raw": response.text}

    if not response.is_success:
        raise HTTPException(
            status_code=response.status_code,
            detail={
                "message": "Pricing webhook returned an error.",
                "upstream": upstream_data,
            },
        )

    return upstream_data


@router.post("/webhooks/ride-completed", status_code=status.HTTP_200_OK)
async def webhook_ride_completed(payload: dict):
    return {"accepted": True, "workflow": "ride-completed", "payload": payload}


@router.post("/webhooks/payment-failed", status_code=status.HTTP_200_OK)
async def webhook_payment_failed(payload: dict):
    return {"accepted": True, "workflow": "payment-failed", "payload": payload}


@router.post("/webhooks/driver-signup", status_code=status.HTTP_200_OK)
async def webhook_driver_signup(payload: dict):
    return {"accepted": True, "workflow": "driver-signup", "payload": payload}
