"""Модель User Service."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UserModel:
    id: str
    name: str
    email: str
    role: str
    team_id: Optional[str]
    expertise: Optional[str]
