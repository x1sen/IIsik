"""Тесты устойчивости (timeout, retry, обработка ошибок gRPC/Kafka), Redis-кеша и логирования (ЛР № 7)."""

from __future__ import annotations

import fakeredis
import grpc
import pytest

from gateway.clients.grpc_clients import build_grpc_clients
from kafka_layer.events import TOPIC_HYPOTHESIS_CREATED
from services.business_operations import BusinessOperations
from shared.exceptions import EntityNotFoundError, ServiceUnavailableError
from shared.logging_config import clear_recent_logs, get_recent_logs
from shared.resilience import RetryPolicy, execute_with_retry


class _FakeRpcError(grpc.RpcError):
    def __init__(self, status_code: grpc.StatusCode, detail: str) -> None:
        super().__init__()
        self._code = status_code
        self._detail = detail

    def code(self) -> grpc.StatusCode:
        return self._code

    def details(self) -> str:
        return self._detail


@pytest.fixture()
def resilient_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PDP_DATA_DIR", str(tmp_path))
    clear_recent_logs()
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    clients = build_grpc_clients(
        redis_client=redis_client,
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=0.01, timeout_seconds=2.0),
    )
    yield clients, redis_client
    clients.shutdown()


def test_retry_succeeds_after_transient_error_and_stops_on_timeout():
    clear_recent_logs()
    attempts = {"n": 0}

    def flaky_call(_timeout: float) -> str:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise _FakeRpcError(grpc.StatusCode.UNAVAILABLE, "Временный сбой канала")
        return "ok"

    res = execute_with_retry(
        "TestService.FlakyCall",
        RetryPolicy(max_attempts=3, backoff_seconds=0.0, timeout_seconds=1.5),
        flaky_call,
    )
    assert res == "ok"
    assert attempts["n"] == 3

    timeout_attempts = {"n": 0}

    def always_timeout(_timeout: float) -> str:
        timeout_attempts["n"] += 1
        raise _FakeRpcError(grpc.StatusCode.DEADLINE_EXCEEDED, "Превышен timeout")

    with pytest.raises(ServiceUnavailableError):
        execute_with_retry(
            "TestService.SlowCall",
            RetryPolicy(max_attempts=2, backoff_seconds=0.0, timeout_seconds=0.5),
            always_timeout,
        )
    assert timeout_attempts["n"] == 2

    not_found_attempts = {"n": 0}

    def not_found_call(_timeout: float) -> str:
        not_found_attempts["n"] += 1
        raise _FakeRpcError(grpc.StatusCode.NOT_FOUND, "missing-id")

    with pytest.raises(EntityNotFoundError):
        execute_with_retry(
            "TestService.GetMissing",
            RetryPolicy(max_attempts=3, backoff_seconds=0.0, timeout_seconds=1.0),
            not_found_call,
        )
    assert not_found_attempts["n"] == 1

    logs = "\n".join(get_recent_logs())
    assert "gRPC RETRY op=TestService.FlakyCall" in logs
    assert "gRPC ERROR op=TestService.SlowCall" in logs


def test_redis_caching_and_kafka_invalidation(resilient_env):
    clients, redis_client = resilient_env
    clear_recent_logs()

    p1 = clients.product.get_product("prod-001")
    assert p1.name == "Онлайн-кредитование"
    assert redis_client.get("cache:product:prod-001") is not None

    p2 = clients.product.get_product("prod-001")
    assert p2.name == "Онлайн-кредитование"

    s1 = clients.hypothesis.get_summary()
    assert s1.total_count == 3
    s2 = clients.hypothesis.get_summary()
    assert s2.total_count == 3

    ops = BusinessOperations(clients)
    ops.create_hypothesis(
        title="Кешируемая проверка гипотезы",
        description="Проверка инвалидации кеша через Kafka",
        product_id="prod-001",
        owner_id="user-001",
        priority="P1",
        if_action="обновить сводку",
        then_result="кеш инвалидируется",
        because_assumption="Kafka consumer сбрасывает устаревший кеш",
    )

    s3 = clients.hypothesis.get_summary()
    assert s3.total_count == 4

    logs = "\n".join(get_recent_logs())
    assert "CACHE MISS key=cache:product:prod-001" in logs
    assert "CACHE HIT key=cache:product:prod-001" in logs
    assert "CACHE INVALIDATE prefix=cache:summary:" in logs
    assert "BIZ START create_hypothesis" in logs
    assert "KAFKA PUBLISH topic=HypothesisCreated" in logs
    assert "KAFKA CONSUME OK topic=HypothesisCreated" in logs


def test_kafka_consumer_error_isolated_to_dlq_and_export_rollback(resilient_env, monkeypatch):
    clients, _ = resilient_env

    def broken_handler(_env):
        raise RuntimeError("Сбой стороннего обработчика")

    clients.kafka_consumer.register(TOPIC_HYPOTHESIS_CREATED, broken_handler)

    ops = BusinessOperations(clients)
    hyp = ops.create_hypothesis(
        title="Проверка DLQ при сбое потребителя",
        description="Система не должна падать при ошибке одного consumer",
        product_id="prod-001",
        owner_id="user-001",
        priority="P2",
        if_action="вызвать сбой обработчика",
        then_result="сообщение попадёт в DLQ",
        because_assumption="ошибки Kafka изолированы",
    )
    assert len(clients.kafka_producer.broker.dead_letter_queue) >= 1
    assert any(l.action == "CREATED" for l in clients.audit.list_activity_logs("HYPOTHESIS", hyp.id))

    def failing_external(hypothesis_id: str, idempotency_key: str):
        raise ServiceUnavailableError("Внешний трекер недоступен")

    monkeypatch.setattr(clients.integration, "create_external_task", failing_external)
    with pytest.raises(ServiceUnavailableError):
        ops.export_to_backlog("hyp-002", "user-001")

    restored = clients.hypothesis.get_hypothesis("hyp-002")
    assert restored.status == "CONFIRMED"
