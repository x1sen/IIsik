"""Точка входа FastAPI + Strawberry GraphQL Gateway."""

from __future__ import annotations

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from gateway.clients.mocks import ServiceClients, build_mock_clients
from gateway.config import GatewayConfig
from gateway.schema import schema


def create_app(clients: ServiceClients | None = None) -> FastAPI:
    cfg = GatewayConfig()
    active_clients = clients or build_mock_clients()

    def get_context() -> dict:
        return {"clients": active_clients}

    graphql_app = GraphQLRouter(schema, context_getter=get_context)
    app = FastAPI(title=cfg.app_name)
    app.include_router(graphql_app, prefix="/graphql")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "mock-clients" if cfg.use_mock_clients else "grpc"}

    return app


app = create_app()
