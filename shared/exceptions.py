"""Общие исключения доменного и сервисного слоёв."""


class ServiceError(Exception):
    """Базовое исключение сервиса."""


class EntityNotFoundError(ServiceError):
    """Сущность не найдена в базе данных сервиса."""

    def __init__(self, entity: str, entity_id: str) -> None:
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} с идентификатором '{entity_id}' не найден(а)")


class ValidationError(ServiceError):
    """Ошибка валидации входных параметров."""


class BusinessRuleError(ServiceError):
    """Нарушение бизнес-правила или недопустимый переход состояния."""


class AuthenticationError(ServiceError):
    """Ошибка аутентификации или отсутствия активной сессии."""


class AuthorizationError(ServiceError):
    """Недостаточно прав для выполнения операции."""
