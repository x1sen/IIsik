"""Конвертеры моделей в protobuf и обработка ошибок gRPC."""

from __future__ import annotations

from functools import wraps

import grpc

from protos import platform_pb2
from shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    EntityNotFoundError,
    ValidationError,
)


def grpc_error_guard(fn):
    @wraps(fn)
    def wrapper(self, request, context):
        try:
            return fn(self, request, context)
        except EntityNotFoundError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        except ValidationError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except BusinessRuleError as exc:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        except AuthenticationError as exc:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, str(exc))
        except AuthorizationError as exc:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, str(exc))

    return wrapper


def hyp_to_proto(h) -> platform_pb2.HypothesisProto:
    return platform_pb2.HypothesisProto(
        id=h.id,
        title=h.title,
        description=h.description,
        status=h.status,
        priority=h.priority,
        has_rice_score=h.rice_score is not None,
        rice_score=float(h.rice_score) if h.rice_score is not None else 0.0,
        product_id=h.product_id,
        owner_id=h.owner_id,
        created_at=h.created_at,
    )


def res_to_proto(r) -> platform_pb2.ResearchProto:
    return platform_pb2.ResearchProto(
        id=r.id,
        title=r.title,
        status=r.status,
        type=r.type,
        method=r.method,
        target_audience=r.target_audience,
        sample_size=r.sample_size,
        start_date=r.start_date or "",
        end_date=r.end_date or "",
        hypothesis_id=r.hypothesis_id,
        assignee_id=r.assignee_id,
    )


def rice_to_proto(s) -> platform_pb2.RICEScoreProto:
    if s is None:
        return platform_pb2.RICEScoreProto(found=False)
    return platform_pb2.RICEScoreProto(
        found=True,
        id=s.id,
        hypothesis_id=s.hypothesis_id,
        reach=s.reach,
        impact=s.impact,
        confidence=s.confidence,
        effort=s.effort,
        calculated_score=s.calculated_score,
    )


def report_to_proto(rep) -> platform_pb2.ReportProto:
    if rep is None:
        return platform_pb2.ReportProto(found=False)
    return platform_pb2.ReportProto(
        found=True,
        id=rep.id,
        research_id=rep.research_id,
        conclusion=rep.conclusion,
        recommendations=rep.recommendations,
        file_url=rep.file_url or "",
        created_at=rep.created_at,
    )


def backlog_to_proto(t) -> platform_pb2.BacklogTaskProto:
    if t is None:
        return platform_pb2.BacklogTaskProto(found=False)
    return platform_pb2.BacklogTaskProto(
        found=True,
        id=t.id,
        hypothesis_id=t.hypothesis_id,
        idempotency_key=t.idempotency_key,
        external_system=t.external_system,
        external_key=t.external_key,
        external_url=t.external_url,
        status=t.status,
        synced_at=t.synced_at,
    )
