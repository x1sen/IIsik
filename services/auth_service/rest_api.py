"""REST API-маршруты Auth Service (/auth/register, /auth/login, /auth/verify, /auth/logout)."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from services.auth_service.service import AuthService
from shared.exceptions import AuthenticationError, ValidationError


class RegisterPayload(BaseModel):
    name: str
    email: str
    password: str
    role: str = "PM"


class LoginPayload(BaseModel):
    email: str
    password: str


def build_auth_router(auth_service: AuthService) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/register")
    def register(body: RegisterPayload) -> dict:
        try:
            res = auth_service.register(body.name, body.email, body.password, body.role)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "access_token": res.access_token,
            "token_type": res.token_type,
            "session_id": res.session_id,
            "expires_in": res.expires_in,
            "user_id": res.user.id,
            "role": res.user.role,
        }

    @router.post("/login")
    def login(body: LoginPayload) -> dict:
        try:
            res = auth_service.login(body.email, body.password)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        return {
            "access_token": res.access_token,
            "token_type": res.token_type,
            "session_id": res.session_id,
            "expires_in": res.expires_in,
            "user_id": res.user.id,
            "role": res.user.role,
        }

    @router.get("/verify")
    def verify(authorization: str = Header(default="")) -> dict:
        token = authorization.removeprefix("Bearer ").strip()
        try:
            user = auth_service.verify_token_and_session(token)
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        return {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "session_id": user.session_id,
        }

    @router.post("/logout")
    def logout(authorization: str = Header(default="")) -> dict:
        token = authorization.removeprefix("Bearer ").strip()
        try:
            auth_service.logout(token)
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        return {"logged_out": True}

    return router
