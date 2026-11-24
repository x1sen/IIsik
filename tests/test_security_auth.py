"""Тесты безопасности: Auth Service, JWT, Redis-сессии (TTL, logout) и RBAC (ЛР № 5)."""

from __future__ import annotations

import time

import fakeredis
import pytest
from fastapi.testclient import TestClient

from gateway.app import create_app
from gateway.clients.mocks import build_mock_clients


@pytest.fixture()
def secured_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PDP_DATA_DIR", str(tmp_path))
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    clients = build_mock_clients(redis_client=redis_client, session_ttl_seconds=60)
    app = create_app(clients=clients)
    return TestClient(app), clients, redis_client


def _gql(tc: TestClient, query: str, token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = tc.post("/graphql", json={"query": query}, headers=headers)
    assert resp.status_code == 200
    return resp.json()


def test_unauthenticated_access_is_denied(secured_env):
    tc, _, _ = secured_env
    q = _gql(tc, 'query { hypothesis(id: "hyp-002") { id title } }')
    assert "errors" in q
    assert "авториз" in q["errors"][0]["message"].lower()

    m = _gql(tc, 'mutation { exportToBacklog(input: { hypothesisId: "hyp-002" }) { externalKey } }')
    assert "errors" in m
    assert "авториз" in m["errors"][0]["message"].lower()


def test_register_login_password_hash_and_me(secured_env):
    tc, clients, redis_client = secured_env
    reg_mut = """
    mutation {
      register(input: {
        name: "Иван Новиков"
        email: "novikov@bank.local"
        password: "secret_password"
        role: PM
      }) {
        accessToken
        tokenType
        sessionId
        expiresIn
        user { id email role }
      }
    }
    """
    res = _gql(tc, reg_mut)
    assert "errors" not in res
    payload = res["data"]["register"]
    assert payload["tokenType"] == "Bearer"
    assert payload["user"]["role"] == "PM"
    token = payload["accessToken"]
    sid = payload["sessionId"]

    assert redis_client.get(f"session:{sid}") is not None
    stored_user = clients.auth_service._repo.get_by_email("novikov@bank.local")
    assert stored_user is not None
    assert stored_user.password_hash != "secret_password"
    assert stored_user.password_hash.startswith("pbkdf2_sha256$")

    me_res = _gql(tc, "query { me { id name email role } }", token=token)
    assert "errors" not in me_res
    assert me_res["data"]["me"]["email"] == "novikov@bank.local"

    bad_login = _gql(
        tc,
        'mutation { login(input: { email: "novikov@bank.local", password: "wrong" }) { accessToken } }',
    )
    assert "errors" in bad_login


def test_jwt_rejected_when_redis_session_missing_or_expired(tmp_path, monkeypatch):
    monkeypatch.setenv("PDP_DATA_DIR", str(tmp_path))
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    clients = build_mock_clients(redis_client=redis_client, session_ttl_seconds=1)
    tc = TestClient(create_app(clients=clients))

    login_res = _gql(
        tc,
        'mutation { login(input: { email: "smirnov@bank.local", password: "pm_pass123" }) { accessToken sessionId } }',
    )
    assert "errors" not in login_res
    token = login_res["data"]["login"]["accessToken"]

    ok_res = _gql(tc, "query { me { email } }", token=token)
    assert "errors" not in ok_res

    time.sleep(1.2)
    expired_res = _gql(tc, "query { me { email } }", token=token)
    assert "errors" in expired_res
    assert "сессия" in expired_res["errors"][0]["message"].lower() or "истёк" in expired_res["errors"][0]["message"].lower()


def test_logout_invalidates_redis_session_for_valid_jwt(secured_env):
    tc, _, _ = secured_env
    login_res = _gql(
        tc,
        'mutation { login(input: { email: "smirnov@bank.local", password: "pm_pass123" }) { accessToken } }',
    )
    token = login_res["data"]["login"]["accessToken"]

    out_res = _gql(tc, "mutation { logout }", token=token)
    assert "errors" not in out_res
    assert out_res["data"]["logout"] is True

    after_logout = _gql(tc, 'query { hypothesis(id: "hyp-002") { id } }', token=token)
    assert "errors" in after_logout
    assert "сессия" in after_logout["errors"][0]["message"].lower()


def test_rbac_restricts_queries_and_mutations_by_role(secured_env):
    tc, _, _ = secured_env

    cx_login = _gql(
        tc,
        'mutation { login(input: { email: "kuznetsova@bank.local", password: "cx_pass123" }) { accessToken } }',
    )
    cx_token = cx_login["data"]["login"]["accessToken"]

    pm_login = _gql(
        tc,
        'mutation { login(input: { email: "smirnov@bank.local", password: "pm_pass123" }) { accessToken } }',
    )
    pm_token = pm_login["data"]["login"]["accessToken"]

    cx_export = _gql(
        tc,
        'mutation { exportToBacklog(input: { hypothesisId: "hyp-002" }) { externalKey } }',
        token=cx_token,
    )
    assert "errors" in cx_export
    assert "доступ запрещён" in cx_export["errors"][0]["message"].lower()

    cx_logs = _gql(
        tc,
        'query { activityLogs(entityType: "HYPOTHESIS", entityId: "hyp-002") { id action } }',
        token=cx_token,
    )
    assert "errors" in cx_logs
    assert "доступ запрещён" in cx_logs["errors"][0]["message"].lower()

    pm_research = _gql(
        tc,
        'mutation { addResearchNote(input: { researchId: "res-001", text: "Попытка PM" }) { id } }',
        token=pm_token,
    )
    assert "errors" in pm_research
    assert "доступ запрещён" in pm_research["errors"][0]["message"].lower()

    cx_note = _gql(
        tc,
        'mutation { addResearchNote(input: { researchId: "res-001", text: "Заметка CX" }) { id text } }',
        token=cx_token,
    )
    assert "errors" not in cx_note
    assert cx_note["data"]["addResearchNote"]["text"] == "Заметка CX"
