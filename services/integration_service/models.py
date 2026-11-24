"""Модель Integration Service."""
from dataclasses import dataclass


@dataclass(frozen=True)
class BacklogTaskModel:
    id: str
    hypothesis_id: str
    idempotency_key: str
    external_system: str
    external_key: str
    external_url: str
    status: str
    synced_at: str
