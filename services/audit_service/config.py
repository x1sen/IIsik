"""Конфигурация Audit Service."""
from dataclasses import dataclass
from shared.db import get_db_path


@dataclass(frozen=True)
class AuditServiceConfig:
    service_name: str = "audit-service"
    db_filename: str = "audit.db"

    @property
    def db_path(self):
        return get_db_path(self.db_filename)
