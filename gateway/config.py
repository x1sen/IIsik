"""Конфигурация GraphQL API Gateway."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GatewayConfig:
    app_name: str = "Product Discovery Platform - GraphQL Gateway"
    host: str = os.environ.get("PDP_GATEWAY_HOST", "127.0.0.1")
    port: int = int(os.environ.get("PDP_GATEWAY_PORT", "8000"))
    use_mock_clients: bool = True
