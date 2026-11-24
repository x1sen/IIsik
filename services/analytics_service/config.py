"""Конфигурация Analytics Service."""
from dataclasses import dataclass
from shared.db import get_db_path


@dataclass(frozen=True)
class AnalyticsServiceConfig:
    service_name: str = "analytics-service"
    db_filename: str = "analytics.db"

    @property
    def db_path(self):
        return get_db_path(self.db_filename)
