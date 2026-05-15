from __future__ import annotations

import pytest

from app.config import Settings
from services.integrations import N8NWebhookService


class DummyResponse:
    def raise_for_status(self) -> None:
        return None


class DummyAsyncClient:
    def __init__(self, *args, **kwargs) -> None:
        self.timeout = kwargs.get("timeout")
        self.post_called = False
        self.request_args = None
        self.request_kwargs = None

    async def __aenter__(self) -> "DummyAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        self.post_called = True
        self.request_args = args
        self.request_kwargs = kwargs
        return DummyResponse()


@pytest.mark.asyncio
async def test_send_event_does_nothing_when_n8n_url_is_missing() -> None:
    settings = Settings(database_url="postgresql://localhost/db", jwt_secret="secret")
    service = N8NWebhookService(settings)

    await service.send_event("ride_requested", {"ride_id": "1"})


@pytest.mark.asyncio
async def test_send_event_posts_to_n8n_webhook(monkeypatch) -> None:
    settings = Settings(
        database_url="postgresql://localhost/db",
        jwt_secret="secret",
        n8n_webhook_url="https://example.com/webhook",
        n8n_webhook_secret="secret",
        n8n_webhook_timeout_sec=2,
    )
    service = N8NWebhookService(settings)
    client = DummyAsyncClient()

    def dummy_async_client(*args, **kwargs):
        assert kwargs["timeout"] == 2
        return client

    monkeypatch.setattr("services.integrations.httpx.AsyncClient", dummy_async_client)

    await service.send_event("ride_accepted", {"ride_id": "1"})

    assert client.post_called
    assert client.request_args[0] == "https://example.com/webhook"
    assert client.request_kwargs["json"]["event"] == "ride_accepted"
    assert client.request_kwargs["json"]["payload"]["ride_id"] == "1"
    assert client.request_kwargs["json"]["ride_id"] == "1"
    assert client.request_kwargs["headers"]["X-N8N-Webhook-Secret"] == "secret"
