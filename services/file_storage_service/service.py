"""Сервисный слой File Storage Service."""
from services.file_storage_service.models import AttachmentModel
from services.file_storage_service.repository import FileStorageRepository


class FileStorageService:
    def __init__(self, repo: FileStorageRepository) -> None:
        self._repo = repo

    def list_attachments(self, entity_type: str, entity_id: str) -> list[AttachmentModel]:
        return self._repo.list_by_entity(entity_type=entity_type, entity_id=entity_id)
