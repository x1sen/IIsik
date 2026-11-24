"""Точка входа FastAPI + Strawberry GraphQL Gateway (gRPC + Kafka)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from strawberry.fastapi import GraphQLRouter

from gateway.clients.grpc_clients import ServiceClients, build_grpc_clients
from gateway.config import GatewayConfig
from gateway.schema import schema
from services.auth_service.rest_api import build_auth_router


def create_app(clients: ServiceClients | None = None) -> FastAPI:
    cfg = GatewayConfig()
    active_clients = clients or build_grpc_clients()

    def get_context(request: Request) -> dict:
        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
        return {"clients": active_clients, "auth_token": token}

    graphql_app = GraphQLRouter(schema, context_getter=get_context)
    app = FastAPI(title=cfg.app_name)
    app.include_router(graphql_app, prefix="/graphql")
    app.include_router(build_auth_router(active_clients.auth_service))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "mode": "grpc+kafka",
            "resilience": "timeout+retry+redis-cache",
        }

    return app


app = create_app()
