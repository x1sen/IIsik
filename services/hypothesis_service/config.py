"""Конфигурация Hypothesis Service."""

from dataclasses import dataclass
from shared.db import get_db_path


@dataclass(frozen=True)
class HypothesisServiceConfig:
    service_name: str = "hypothesis-service"
    db_filename: str = "hypothesis.db"

    @property
    def db_path(self):
        return get_db_path(self.db_filename)
