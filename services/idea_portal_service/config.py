"""Конфигурация Idea Portal Service."""
from dataclasses import dataclass
from shared.db import get_db_path


@dataclass(frozen=True)
class IdeaPortalServiceConfig:
    service_name: str = "idea-portal-service"
    db_filename: str = "idea.db"

    @property
    def db_path(self):
        return get_db_path(self.db_filename)
