"""Конфигурация Auth Service."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AuthServiceConfig:
    service_name: str = "auth_service"
    db_filename: str = "auth.sqlite3"
    jwt_secret: str = os.environ.get("PDP_JWT_SECRET", "pdp-lab5-dev-secret-key-change-in-prod-32b")
    jwt_algorithm: str = "HS256"
    session_ttl_seconds: int = int(os.environ.get("PDP_SESSION_TTL", "3600"))
    redis_url: str = os.environ.get("PDP_REDIS_URL", "redis://localhost:6379/0")
