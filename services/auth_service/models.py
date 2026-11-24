"""Модели Auth Service."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthUserModel:
    id: str
    name: str
    email: str
    password_hash: str
    role: str
    created_at: str


@dataclass(frozen=True)
class AuthenticatedUserModel:
    user_id: str
    name: str
    email: str
    role: str
    session_id: str


@dataclass(frozen=True)
class AuthTokenModel:
    access_token: str
    token_type: str
    session_id: str
    expires_in: int
    user: AuthUserModel
