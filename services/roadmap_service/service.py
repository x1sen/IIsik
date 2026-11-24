"""Сервисный слой Roadmap Service."""
from __future__ import annotations

from datetime import date
import uuid

from services.roadmap_service.models import RoadmapItemModel
from services.roadmap_service.repository import RoadmapRepository
from shared.exceptions import ValidationError


class RoadmapService:
    def __init__(self, repo: RoadmapRepository) -> None:
        self._repo = repo

    def list_roadmap(self, sort_dir: str = "ASC") -> list[RoadmapItemModel]:
        return self._repo.list_items(sort_dir=sort_dir)

    def schedule_item(
        self,
        hypothesis_id: str,
        hypothesis_title: str,
        start_date: str,
        end_date: str,
        dependencies: list[str],
        assignee_id: str,
    ) -> RoadmapItemModel:
        try:
            d_start = date.fromisoformat(start_date)
            d_end = date.fromisoformat(end_date)
        except ValueError as exc:
            raise ValidationError("Даты должны быть в формате YYYY-MM-DD") from exc
        if d_end < d_start:
            raise ValidationError("Дата завершения не может быть раньше даты начала")
        duration = (d_end - d_start).days + 1
        item = RoadmapItemModel(
            id=f"rm-{uuid.uuid4().hex[:8]}",
            hypothesis_id=hypothesis_id,
            hypothesis_title=hypothesis_title,
            start_date=start_date,
            end_date=end_date,
            duration=duration,
            dependencies=dependencies,
            assignee_id=assignee_id,
        )
        return self._repo.save_item(item)

    def update_title_cache(self, hypothesis_id: str, title: str) -> None:
        self._repo.upsert_title_cache(hypothesis_id, title)
