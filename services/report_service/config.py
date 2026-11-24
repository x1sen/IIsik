"""Конфигурация Report Service."""
from dataclasses import dataclass
from shared.db import get_db_path


@dataclass(frozen=True)
class ReportServiceConfig:
    service_name: str = "report-service"
    db_filename: str = "report.db"

    @property
    def db_path(self):
        return get_db_path(self.db_filename)
