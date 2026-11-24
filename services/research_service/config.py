"""Конфигурация Research Service."""

from dataclasses import dataclass
from shared.db import get_db_path


@dataclass(frozen=True)
class ResearchServiceConfig:
    service_name: str = "research-service"
    db_filename: str = "research.db"

    @property
    def db_path(self):
        return get_db_path(self.db_filename)
