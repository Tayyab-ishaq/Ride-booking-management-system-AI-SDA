from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    payment_webhook_secret: str = "dev-payment-webhook-secret"
    n8n_webhook_url: str | None = None
    n8n_pricing_webhook_url: str | None = None
    n8n_webhook_secret: str | None = None
    n8n_webhook_timeout_sec: int = 5
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 10080
    db_pool_min_size: int = 1
    db_pool_max_size: int = 10


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _require_env_any(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    joined_names = ", ".join(names)
    raise RuntimeError(f"Missing required environment variable. Set one of: {joined_names}")


def get_settings() -> Settings:
    return Settings(
        database_url=_require_env_any("DATABASE_URL", "DB_URL"),
        jwt_secret=_require_env("JWT_SECRET"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        payment_webhook_secret=os.getenv("PAYMENT_WEBHOOK_SECRET", "dev-payment-webhook-secret"),
        n8n_webhook_url=os.getenv("N8N_WEBHOOK_URL"),
        n8n_pricing_webhook_url=os.getenv("N8N_PRICING_WEBHOOK_URL"),
        n8n_webhook_secret=os.getenv("N8N_WEBHOOK_SECRET"),
        n8n_webhook_timeout_sec=int(os.getenv("N8N_WEBHOOK_TIMEOUT_SEC", "5")),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
        refresh_token_expire_minutes=int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "10080")),
        db_pool_min_size=int(os.getenv("DB_POOL_MIN_SIZE", "1")),
        db_pool_max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
    )
