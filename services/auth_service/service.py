"""Сервисный слой Auth Service: регистрация, вход, хэширование паролей, JWT и сессии Redis."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
from typing import Optional
import uuid

import jwt

from services.auth_service.config import AuthServiceConfig
from services.auth_service.models import (
    AuthenticatedUserModel,
    AuthTokenModel,
    AuthUserModel,
)
from services.auth_service.repository import AuthRepository
from services.auth_service.session_store import RedisSessionStore
from shared.exceptions import AuthenticationError, ValidationError


_VALID_ROLES = {"PM", "CX_EXPERT", "AGILE_CENTER", "ADMIN"}


def hash_password(password: str) -> str:
    """Хэширование пароля с помощью PBKDF2-HMAC-SHA256 и случайной соли."""
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Проверка пароля без хранения в открытом виде."""
    try:
        algo, salt, expected = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000).hex()
    return hmac.compare_digest(actual, expected)


class AuthService:
    def __init__(
        self,
        repo: AuthRepository,
        session_store: RedisSessionStore,
        config: Optional[AuthServiceConfig] = None,
    ) -> None:
        self._repo = repo
        self._sessions = session_store
        self._cfg = config or AuthServiceConfig()

    def register(
        self, name: str, email: str, password: str, role: str = "PM"
    ) -> AuthTokenModel:
        if not name.strip() or not email.strip():
            raise ValidationError("Имя и email пользователя обязательны")
        if len(password) < 6:
            raise ValidationError("Пароль должен содержать не менее 6 символов")
        if role not in _VALID_ROLES:
            raise ValidationError(f"Недопустимая роль '{role}'")
        if self._repo.get_by_email(email.strip()) is not None:
            raise ValidationError(f"Пользователь с email '{email}' уже зарегистрирован")

        user = AuthUserModel(
            id=f"user-{uuid.uuid4().hex[:8]}",
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=hash_password(password),
            role=role,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        self._repo.create_user(user)
        return self._issue_token_and_session(user)

    def login(self, email: str, password: str) -> AuthTokenModel:
        if not email.strip() or not password:
            raise ValidationError("Email и пароль обязательны")
        user = self._repo.get_by_email(email.strip())
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Неверный email или пароль")
        return self._issue_token_and_session(user)

    def _issue_token_and_session(
        self, user: AuthUserModel, ttl_seconds: Optional[int] = None
    ) -> AuthTokenModel:
        ttl = ttl_seconds if ttl_seconds is not None else self._cfg.session_ttl_seconds
        session_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl)

        self._sessions.create_session(
            session_id=session_id,
            payload={
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "expires_at": expires_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            ttl_seconds=ttl,
        )

        token = jwt.encode(
            {
                "sub": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "sid": session_id,
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
            },
            self._cfg.jwt_secret,
            algorithm=self._cfg.jwt_algorithm,
        )
        return AuthTokenModel(
            access_token=token,
            token_type="Bearer",
            session_id=session_id,
            expires_in=ttl,
            user=user,
        )

    def verify_token_and_session(self, token: str) -> AuthenticatedUserModel:
        if not token or not token.strip():
            raise AuthenticationError("Отсутствует JWT-токен аутентификации")
        try:
            payload = jwt.decode(
                token,
                self._cfg.jwt_secret,
                algorithms=[self._cfg.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError("Срок действия JWT-токена истёк") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError("Недействительный JWT-токен") from exc

        session_id = payload.get("sid")
        if not session_id:
            raise AuthenticationError("В токене отсутствует идентификатор сессии")

        session = self._sessions.get_session(session_id)
        if session is None:
            raise AuthenticationError(
                "Активная сессия отсутствует или истекла в Redis — требуется повторный вход"
            )

        return AuthenticatedUserModel(
            user_id=session["user_id"],
            name=session["name"],
            email=session["email"],
            role=session["role"],
            session_id=session_id,
        )

    def logout(self, token: str) -> bool:
        user = self.verify_token_and_session(token)
        self._sessions.delete_session(user.session_id)
        return True
