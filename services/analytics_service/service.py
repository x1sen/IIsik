"""Сервисный слой Analytics Service."""
from typing import Optional
from services.analytics_service.models import DashboardMetricModel
from services.analytics_service.repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, repo: AnalyticsRepository) -> None:
        self._repo = repo

    def get_dashboard_metrics(
        self, product_id: Optional[str] = None, period: Optional[str] = None
    ) -> list[DashboardMetricModel]:
        return self._repo.list_metrics(product_id=product_id, period=period)

    def handle_hypothesis_event(
        self,
        hypothesis_id: str,
        product_id: str,
        updated_at: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        rice_score: Optional[float] = None,
    ) -> None:
        self._repo.upsert_read_model_and_recalculate(
            hypothesis_id=hypothesis_id,
            product_id=product_id,
            status=status,
            priority=priority,
            rice_score=rice_score,
            updated_at=updated_at,
        )
