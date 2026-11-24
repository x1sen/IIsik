"""Модель Report Service."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ReportModel:
    id: str
    research_id: str
    conclusion: str
    recommendations: str
    file_url: Optional[str]
    created_at: str
