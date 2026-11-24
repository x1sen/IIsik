"""Механизмы устойчивости межсервисных вызовов: timeout и ограниченный retry."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable, TypeVar

import grpc

from shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    EntityNotFoundError,
    ServiceError,
    ServiceUnavailableError,
    ValidationError,
)
from shared.logging_config import get_platform_logger

T = TypeVar("T")
_log = get_platform_logger("pdp.grpc")

RETRYABLE_STATUS_CODES = {
    grpc.StatusCode.UNAVAILABLE,
    grpc.StatusCode.DEADLINE_EXCEEDED,
}


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_seconds: float = 0.05
    timeout_seconds: float = 2.0


def map_grpc_error(exc: grpc.RpcError) -> ServiceError:
    code = exc.code()
    detail = exc.details() or "Ошибка gRPC-вызова"
    if code == grpc.StatusCode.NOT_FOUND:
        return EntityNotFoundError("Объект", detail)
    if code == grpc.StatusCode.INVALID_ARGUMENT:
        return ValidationError(detail)
    if code == grpc.StatusCode.FAILED_PRECONDITION:
        return BusinessRuleError(detail)
    if code == grpc.StatusCode.UNAUTHENTICATED:
        return AuthenticationError(detail)
    if code == grpc.StatusCode.PERMISSION_DENIED:
        return AuthorizationError(detail)
    if code in RETRYABLE_STATUS_CODES:
        return ServiceUnavailableError(f"Сервис временно недоступен ({code.name}): {detail}")
    return ServiceError(f"gRPC ошибка ({code.name}): {detail}")


def execute_with_retry(
    operation_name: str,
    policy: RetryPolicy,
    call_fn: Callable[[float], T],
) -> T:
    """Выполняет gRPC-вызов с timeout, ограниченным retry для временных сбоев и логированием."""
    last_exc: grpc.RpcError | None = None
    for attempt in range(1, max(1, policy.max_attempts) + 1):
        started = time.perf_counter()
        try:
            result = call_fn(policy.timeout_seconds)
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            _log.info("gRPC OK op=%s attempt=%d duration_ms=%.2f", operation_name, attempt, elapsed_ms)
            return result
        except grpc.RpcError as exc:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            code = exc.code()
            last_exc = exc
            if code in RETRYABLE_STATUS_CODES and attempt < policy.max_attempts:
                _log.warning(
                    "gRPC RETRY op=%s attempt=%d/%d code=%s duration_ms=%.2f detail=%s",
                    operation_name,
                    attempt,
                    policy.max_attempts,
                    code.name,
                    elapsed_ms,
                    exc.details(),
                )
                if policy.backoff_seconds > 0:
                    time.sleep(policy.backoff_seconds * attempt)
                continue
            _log.error(
                "gRPC ERROR op=%s attempt=%d code=%s duration_ms=%.2f detail=%s",
                operation_name,
                attempt,
                code.name,
                elapsed_ms,
                exc.details(),
            )
            raise map_grpc_error(exc) from exc
    assert last_exc is not None
    raise map_grpc_error(last_exc)
