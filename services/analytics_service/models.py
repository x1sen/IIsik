"""Модели Analytics Service."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DashboardMetricModel:
    id: str
    metric_type: str
    product_id: str
    period: str
    value: float


@dataclass(frozen=True)
class AnalyticsReadModel:
    hypothesis_id: str
    product_id: str
    status: str
    priority: str
    rice_score: Optional[float]
    updated_at: str
