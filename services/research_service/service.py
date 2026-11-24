"""Сервисный слой Research Service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import uuid

from services.research_service.models import (
    InsightModel,
    ResearchDesignModel,
    ResearchModel,
    ResearchNoteModel,
)
from services.research_service.repository import ResearchRepository
from shared.exceptions import BusinessRuleError, EntityNotFoundError, ValidationError


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class ResearchService:
    def __init__(self, repo: ResearchRepository) -> None:
        self._repo = repo

    def get_research(self, research_id: str) -> ResearchModel:
        item = self._repo.get_by_id(research_id)
        if item is None:
            raise EntityNotFoundError("Исследование", research_id)
        return item

    def list_researches(
        self,
        hypothesis_id: Optional[str] = None,
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
        sort_by: str = "start_date",
        sort_dir: str = "DESC",
    ) -> list[ResearchModel]:
        return self._repo.list_researches(
            hypothesis_id=hypothesis_id,
            status=status,
            assignee_id=assignee_id,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    def get_design(self, research_id: str) -> Optional[ResearchDesignModel]:
        return self._repo.get_design(research_id)

    def list_insights(self, research_id: str) -> list[InsightModel]:
        return self._repo.list_insights(research_id)

    def list_notes(self, research_id: str) -> list[ResearchNoteModel]:
        return self._repo.list_notes(research_id)

    def create_research(
        self,
        hypothesis_id: str,
        title: str,
        research_type: str,
        method: str,
        target_audience: str,
        sample_size: int,
        assignee_id: str,
        goal: str,
        questions: str,
        success_criteria: str,
        user_stories: Optional[str] = None,
    ) -> ResearchModel:
        if not title.strip() or not goal.strip():
            raise ValidationError("Название и цель исследования обязательны")
        if sample_size <= 0:
            raise ValidationError("Размер выборки (sample_size) должен быть больше нуля")
        res_id = f"res-{uuid.uuid4().hex[:8]}"
        research = ResearchModel(
            id=res_id,
            title=title.strip(),
            status="PLANNED",
            type=research_type,
            method=method.strip(),
            target_audience=target_audience.strip(),
            sample_size=sample_size,
            start_date=_today_iso(),
            end_date=None,
            hypothesis_id=hypothesis_id,
            assignee_id=assignee_id,
        )
        design = ResearchDesignModel(
            id=f"des-{uuid.uuid4().hex[:8]}",
            research_id=res_id,
            goal=goal.strip(),
            questions=questions.strip(),
            success_criteria=success_criteria.strip(),
            user_stories=user_stories,
        )
        return self._repo.create_research(research, design)

    def add_note(self, research_id: str, author_id: str, text: str) -> ResearchNoteModel:
        research = self.get_research(research_id)
        if research.status == "COMPLETED":
            raise BusinessRuleError("Нельзя добавлять заметки в завершённое исследование")
        if not text.strip():
            raise ValidationError("Текст заметки не может быть пустым")
        new_status = "IN_PROGRESS" if research.status == "PLANNED" else None
        note = ResearchNoteModel(
            id=f"note-{uuid.uuid4().hex[:8]}",
            research_id=research_id,
            text=text.strip(),
            author_id=author_id,
            created_at=_now_iso(),
        )
        return self._repo.add_note(note, new_status=new_status)

    def add_insight(self, research_id: str, created_by: str, text: str) -> InsightModel:
        research = self.get_research(research_id)
        if research.status == "COMPLETED":
            raise BusinessRuleError("Нельзя добавлять инсайты в завершённое исследование")
        if not text.strip():
            raise ValidationError("Текст инсайта не может быть пустым")
        new_status = "IN_PROGRESS" if research.status == "PLANNED" else None
        insight = InsightModel(
            id=f"ins-{uuid.uuid4().hex[:8]}",
            research_id=research_id,
            text=text.strip(),
            created_by=created_by,
            created_at=_now_iso(),
        )
        return self._repo.add_insight(insight, new_status=new_status)

    def complete_research(self, research_id: str) -> ResearchModel:
        research = self.get_research(research_id)
        if research.status in {"REPORT_READY", "COMPLETED"}:
            raise BusinessRuleError(f"Исследование уже имеет статус {research.status}")
        return self._repo.update_status(research_id, "REPORT_READY", end_date=_today_iso())

    def mark_completed(self, research_id: str) -> ResearchModel:
        research = self.get_research(research_id)
        if research.status != "REPORT_READY":
            raise BusinessRuleError(
                f"Нельзя завершить исследование без готового отчёта (текущий статус: {research.status})"
            )
        return self._repo.update_status(research_id, "COMPLETED")
