"""Сервисный слой Audit Service."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import uuid

from services.audit_service.models import ActivityLogModel
from services.audit_service.repository import AuditRepository


class AuditService:
    def __init__(self, repo: AuditRepository) -> None:
        self._repo = repo

    def list_activity_logs(self, entity_type: str, entity_id: str) -> list[ActivityLogModel]:
        return self._repo.list_logs(entity_type=entity_type, entity_id=entity_id)

    def record_action(
        self,
        entity_type: str,
        entity_id: str,
        user_id: str,
        action: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
    ) -> ActivityLogModel:
        log = ActivityLogModel(
            id=f"log-{uuid.uuid4().hex[:8]}",
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        return self._repo.create_log(log)
