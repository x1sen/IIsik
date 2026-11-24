"""Модели Roadmap Service."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RoadmapItemModel:
    id: str
    hypothesis_id: str
    hypothesis_title: str
    start_date: str
    end_date: str
    duration: int
    dependencies: list[str]
    assignee_id: str
