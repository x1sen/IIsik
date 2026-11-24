"""Конфигурация Integration Service."""
from dataclasses import dataclass
from shared.db import get_db_path


@dataclass(frozen=True)
class IntegrationServiceConfig:
    service_name: str = "integration-service"
    db_filename: str = "integration.db"

    @property
    def db_path(self):
        return get_db_path(self.db_filename)
