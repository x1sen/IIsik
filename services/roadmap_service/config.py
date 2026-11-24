"""Конфигурация Roadmap Service."""
from dataclasses import dataclass
from shared.db import get_db_path


@dataclass(frozen=True)
class RoadmapServiceConfig:
    service_name: str = "roadmap-service"
    db_filename: str = "roadmap.db"

    @property
    def db_path(self):
        return get_db_path(self.db_filename)
