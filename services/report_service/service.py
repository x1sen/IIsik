"""Сервисный слой Report Service."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import uuid

from services.report_service.models import ReportModel
from services.report_service.repository import ReportRepository
from shared.exceptions import BusinessRuleError, EntityNotFoundError, ValidationError


class ReportService:
    def __init__(self, repo: ReportRepository) -> None:
        self._repo = repo

    def get_report(self, report_id: str) -> ReportModel:
        item = self._repo.get_by_id(report_id)
        if item is None:
            raise EntityNotFoundError("Отчёт", report_id)
        return item

    def get_report_by_research(self, research_id: str) -> ReportModel | None:
        return self._repo.get_by_research(research_id)

    def publish_report(
        self,
        research_id: str,
        conclusion: str,
        recommendations: str,
        file_url: Optional[str] = None,
    ) -> ReportModel:
        if not conclusion.strip() or not recommendations.strip():
            raise ValidationError("Заключение и рекомендации отчёта обязательны")
        if self._repo.get_by_research(research_id) is not None:
            raise BusinessRuleError(f"Отчёт для исследования '{research_id}' уже опубликован")
        report = ReportModel(
            id=f"rep-{uuid.uuid4().hex[:8]}",
            research_id=research_id,
            conclusion=conclusion.strip(),
            recommendations=recommendations.strip(),
            file_url=file_url,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        return self._repo.create_report(report)
