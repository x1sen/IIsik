"""Тесты реального gRPC-взаимодействия и событийной интеграции через Kafka (ЛР № 6)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gateway.app import create_app
from gateway.clients.grpc_clients import build_grpc_clients
from kafka_layer.events import (
    TOPIC_HYPOTHESIS_CREATED,
    TOPIC_HYPOTHESIS_PRIORITIZED,
)
from shared.exceptions import EntityNotFoundError


@pytest.fixture()
def integrated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PDP_DATA_DIR", str(tmp_path))
    clients = build_grpc_clients()
    app = create_app(clients=clients)
    tc = TestClient(app)
    login_resp = tc.post(
        "/auth/login", json={"email": "orlova@bank.local", "password": "admin_pass123"}
    )
    assert login_resp.status_code == 200
    tc.headers["Authorization"] = f"Bearer {login_resp.json()['access_token']}"
    yield tc, clients
    clients.shutdown()


def test_grpc_direct_calls_and_not_found_mapping(integrated_env):
    _, clients = integrated_env
    hyp = clients.hypothesis.get_hypothesis("hyp-002")
    assert hyp.id == "hyp-002"
    prod = clients.product.get_product(hyp.product_id)
    assert prod.name == "Дебетовые карты"

    with pytest.raises(EntityNotFoundError):
        clients.hypothesis.get_hypothesis("hyp-nonexistent")


def test_kafka_events_published_and_consumed_in_business_scenarios(integrated_env):
    tc, clients = integrated_env

    create_mut = """
    mutation {
      createHypothesis(input: {
        title: "Кэшбэк за автоплатежи ЖКХ"
        description: "Начислять 2% кэшбэка за подключённые автоплатежи"
        productId: "prod-001"
        ownerId: "user-001"
        priority: P1
        ifAction: "включить 2% кэшбэка за автоплатежи"
        thenResult: "доля регулярных автоплатежей вырастет на 12%"
        becauseAssumption: "клиенты охотнее настраивают автосписание при выгоде"
      }) {
        id
        status
      }
    }
    """
    r1 = tc.post("/graphql", json={"query": create_mut}).json()
    assert "errors" not in r1
    hyp_id = r1["data"]["createHypothesis"]["id"]

    created_events = clients.kafka_producer.broker.get_events(TOPIC_HYPOTHESIS_CREATED)
    assert any(e["hypothesis_id"] == hyp_id for e in created_events)

    logs = clients.audit.list_activity_logs("HYPOTHESIS", hyp_id)
    assert any(l.action == "CREATED" for l in logs)

    notifs = clients.notification.list_notifications("user-001")
    assert any(n.entity_id == hyp_id for n in notifs)

    rice_mut = f"""
    mutation {{
      calculateRICE(input: {{
        hypothesisId: "{hyp_id}", reach: 400, impact: 2.5, confidence: 0.8, effort: 4
      }}) {{
        calculatedScore
      }}
    }}
    """
    r2 = tc.post("/graphql", json={"query": rice_mut}).json()
    assert "errors" not in r2
    assert r2["data"]["calculateRICE"]["calculatedScore"] == 200.0

    prio_events = clients.kafka_producer.broker.get_events(TOPIC_HYPOTHESIS_PRIORITIZED)
    assert any(e["hypothesis_id"] == hyp_id and e["rice_score"] == 200.0 for e in prio_events)

    logs_after = clients.audit.list_activity_logs("HYPOTHESIS", hyp_id)
    assert any(l.action == "PRIORITIZED" for l in logs_after)
