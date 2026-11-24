"""Модуль защиты GraphQL API: делегирует проверку JWT и Redis-сессии в Auth Service и проверяет роли."""

from __future__ import annotations

from typing import Optional

from strawberry.types import Info

from services.auth_service.models import AuthenticatedUserModel
from shared.exceptions import AuthenticationError, AuthorizationError

ALL_ROLES = {"PM", "CX_EXPERT", "AGILE_CENTER", "ADMIN"}
PM_OR_ADMIN = {"PM", "ADMIN"}
CX_OR_ADMIN = {"CX_EXPERT", "ADMIN"}
PM_CX_OR_ADMIN = {"PM", "CX_EXPERT", "ADMIN"}
AGILE_OR_ADMIN = {"AGILE_CENTER", "ADMIN"}


def extract_bearer_token(info: Info) -> str:
    token = (info.context.get("auth_token") or "").strip()
    if not token:
        raise AuthenticationError("Требуется авторизация (заголовок Authorization: Bearer <token>)")
    return token


def require_auth(
    info: Info, allowed_roles: Optional[set[str]] = None
) -> AuthenticatedUserModel:
    """Проверяет JWT и активную сессию в Redis через AuthClient, а затем роль пользователя."""
    token = extract_bearer_token(info)
    user: AuthenticatedUserModel = info.context["clients"].auth.verify_token_and_session(token)
    if allowed_roles is not None and user.role not in allowed_roles:
        raise AuthorizationError(
            f"Доступ запрещён для роли '{user.role}'. Требуется одна из ролей: {sorted(allowed_roles)}"
        )
    return user
