"""Доменные модели Research Service."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ResearchModel:
    id: str
    title: str
    status: str
    type: str
    method: str
    target_audience: str
    sample_size: int
    start_date: Optional[str]
    end_date: Optional[str]
    hypothesis_id: str
    assignee_id: str


@dataclass(frozen=True)
class ResearchDesignModel:
    id: str
    research_id: str
    goal: str
    questions: str
    success_criteria: str
    user_stories: Optional[str]


@dataclass(frozen=True)
class InsightModel:
    id: str
    research_id: str
    text: str
    created_by: str
    created_at: str


@dataclass(frozen=True)
class ResearchNoteModel:
    id: str
    research_id: str
    text: str
    author_id: str
    created_at: str
