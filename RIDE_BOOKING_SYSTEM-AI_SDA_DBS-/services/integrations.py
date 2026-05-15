from __future__ import annotations

import httpx

from app.config import Settings


class N8NWebhookService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.url = settings.n8n_webhook_url
        self.secret = settings.n8n_webhook_secret
        self.timeout = settings.n8n_webhook_timeout_sec

    async def send_event(self, event_name: str, payload: dict) -> None:
        """Send an event payload to the configured n8n webhook URL."""
        if not self.url:
            return

        # Keep both envelope and flat payload keys for workflow compatibility.
        body = {
            "event": event_name,
            "payload": payload,
            **payload,
        }
        headers = {
            "Content-Type": "application/json",
        }
        if self.secret:
            headers["X-N8N-Webhook-Secret"] = self.secret

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.url, json=body, headers=headers)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            # Keep application workflow stable if n8n is temporarily unavailable.
            print(f"n8n webhook failed for event '{event_name}': {exc}")
