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
