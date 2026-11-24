"""Конфигурация GraphQL API Gateway."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GatewayConfig:
    app_name: str = "Product Discovery Platform — GraphQL API"
    host: str = "127.0.0.1"
    port: int = 8000
    use_mock_clients: bool = False
