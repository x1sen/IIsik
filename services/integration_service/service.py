"""Сервисный слой Integration Service."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import uuid

from services.integration_service.models import BacklogTaskModel
from services.integration_service.repository import IntegrationRepository


class IntegrationService:
    def __init__(self, repo: IntegrationRepository) -> None:
        self._repo = repo

    def get_backlog_task(self, hypothesis_id: str) -> Optional[BacklogTaskModel]:
        return self._repo.get_by_hypothesis(hypothesis_id)

    def create_external_task(self, hypothesis_id: str, idempotency_key: str) -> BacklogTaskModel:
        """Идемпотентное создание задачи во внешнем трекере по idempotency_key = hypothesis_id."""
        existing = self._repo.get_by_hypothesis(hypothesis_id)
        if existing is not None:
            return existing
        num = abs(hash(hypothesis_id)) % 900 + 100
        ext_key = f"PD-{num}"
        task = BacklogTaskModel(
            id=f"bt-{uuid.uuid4().hex[:8]}",
            hypothesis_id=hypothesis_id,
            idempotency_key=idempotency_key,
            external_system="TASK_TRACKER",
            external_key=ext_key,
            external_url=f"https://tracker.bank.local/browse/{ext_key}",
            status="OPEN",
            synced_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        return self._repo.create_task(task)
