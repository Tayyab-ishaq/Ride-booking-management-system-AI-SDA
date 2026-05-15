# RIDE_BOOKING_SYSTEM-AI_SDA_DBS-

FastAPI authentication backend for the ride booking system.

## Structure

The project keeps only app bootstrap files in `app/`:

- `app/__init__.py`
- `app/main.py`
- `app/config.py`
- `app/dependencies.py`

Feature and domain modules are top-level packages:

- `api/`
- `core/`
- `db/`
- `exception/`
- `models/`
- `repositories/`
- `schemas/`
- `services/`
- `utils/`
- `tests/`

## Setup

1. Copy `.env.example` to `.env` and set `DB_URL` and `JWT_SECRET`.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run the PostgreSQL migration in [migrations/001_users.sql](migrations/001_users.sql).
4. Start the API with `uvicorn app.main:app --reload`.

## Ride Completion Automation Branch

This branch focuses on automating ride completion workflows and testing ride lifecycle behavior. Key artifacts include:

- `test_matching_status.py` for matching and completion validation
- `run_test_with_server.py` for running integration tests against a live API
- `N8N` workflow files under `n8n_workflows/` for ride completion orchestration

## Auth Routes

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`

## n8n Integration

The app can emit ride lifecycle events to an n8n webhook for email notifications.

Environment variables:

- `N8N_WEBHOOK_URL` — URL of the n8n incoming webhook.
- `N8N_WEBHOOK_SECRET` — optional secret header value sent as `X-N8N-Webhook-Secret`.
- `N8N_WEBHOOK_TIMEOUT_SEC` — request timeout in seconds (default `5`).

Event payloads include:

- `ride_requested`
- `ride_accepted`
- `ride_completed`

Example payload:

```json
{
  "event": "ride_accepted",
  "payload": {
    "ride_id": "...",
    "rider_id": "...",
    "driver_id": "...",
    "status": "accepted"
  }
}
```
