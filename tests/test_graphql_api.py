"""Интеграционные тесты GraphQL API Gateway."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gateway.app import create_app
from gateway.clients.mocks import build_mock_clients


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PDP_DATA_DIR", str(tmp_path))
    app = create_app(clients=build_mock_clients())
    return TestClient(app)


def test_health_endpoint(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_query_hypothesis_with_related_entities(client: TestClient):
    query = """
    query {
      hypothesis(id: "hyp-002") {
        id
        title
        status
        priority
        product { id name owner { id name } }
        owner { id name role }
        template { ifAction thenResult }
        riceScore { calculatedScore }
        backlogTask { externalKey externalUrl status }
      }
    }
    """
    resp = client.post("/graphql", json={"query": query})
    assert resp.status_code == 200
    body = resp.json()
    assert "errors" not in body
    h = body["data"]["hypothesis"]
    assert h["product"]["name"] == "Дебетовые карты"
    assert h["owner"]["role"] == "PM"
    assert h["riceScore"]["calculatedScore"] == 120.0
    assert h["backlogTask"]["externalKey"] == "PD-412"


def test_query_research_and_duplicates_and_lists(client: TestClient):
    query = """
    query {
      research(id: "res-002") {
        id
        title
        status
        hypothesis { id title }
        assignee { id name }
        report { id conclusion fileUrl }
      }
      findDuplicateHypotheses(input: {
        title: "Упрощение анкеты онлайн-кредита",
        description: "Заявка на кредит",
        productId: "prod-001"
      }) {
        hypothesisId
        title
        similarity
      }
      roadmap { id hypothesisTitle duration dependencies assignee { name } }
      dashboardMetrics(productId: "prod-001") { metricType value }
      myNotifications(userId: "user-001", unreadOnly: true) { id message }
      activityLogs(entityType: "HYPOTHESIS", entityId: "hyp-001") { action }
    }
    """
    resp = client.post("/graphql", json={"query": query})
    assert resp.status_code == 200
    body = resp.json()
    assert "errors" not in body
    data = body["data"]
    assert data["research"]["report"]["id"] == "rep-001"
    assert data["findDuplicateHypotheses"][0]["hypothesisId"] == "hyp-001"
    assert len(data["roadmap"]) == 2
    assert len(data["dashboardMetrics"]) == 2
    assert len(data["myNotifications"]) == 1
    assert len(data["activityLogs"]) == 2


def test_query_not_found_returns_graphql_error(client: TestClient):
    query = 'query { hypothesis(id: "missing-id") { id title } }'
    resp = client.post("/graphql", json={"query": query})
    assert resp.status_code == 200
    body = resp.json()
    assert "errors" in body
    assert "missing-id" in body["errors"][0]["message"]
