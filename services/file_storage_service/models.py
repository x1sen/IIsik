"""Модель File Storage Service."""
from dataclasses import dataclass


@dataclass(frozen=True)
class AttachmentModel:
    id: str
    entity_type: str
    entity_id: str
    file_name: str
    file_url: str
    file_size: int
    uploaded_by: str
