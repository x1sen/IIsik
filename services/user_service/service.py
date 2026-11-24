"""Сервисный слой User Service."""
from services.user_service.models import UserModel
from services.user_service.repository import UserRepository
from shared.exceptions import BusinessRuleError, EntityNotFoundError


_ACTION_ROLES: dict[str, set[str]] = {
    "CREATE_HYPOTHESIS": {"PM", "CX_EXPERT", "AGILE_CENTER", "ADMIN"},
    "CALCULATE_RICE": {"PM", "AGILE_CENTER", "ADMIN"},
    "APPLY_RESEARCH_RESULT": {"PM", "CX_EXPERT", "ADMIN"},
    "EXPORT_TO_BACKLOG": {"PM", "ADMIN"},
    "CREATE_RESEARCH": {"CX_EXPERT", "PM", "ADMIN"},
    "PUBLISH_REPORT": {"CX_EXPERT", "ADMIN"},
    "SAVE_PRODUCT": {"ADMIN"},
    "ADD_COMMENT": {"PM", "CX_EXPERT", "AGILE_CENTER", "ADMIN"},
}


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    def get_user(self, user_id: str) -> UserModel:
        item = self._repo.get_by_id(user_id)
        if item is None:
            raise EntityNotFoundError("Пользователь", user_id)
        return item

    def list_users(self) -> list[UserModel]:
        return self._repo.list_users()

    def check_permission(self, user_id: str, action: str) -> UserModel:
        """Проверка существования пользователя и его прав на выполнение бизнес-операции."""
        user = self.get_user(user_id)
        allowed_roles = _ACTION_ROLES.get(action)
        if allowed_roles is not None and user.role not in allowed_roles:
            raise BusinessRuleError(
                f"Роль '{user.role}' пользователя '{user.name}' не разрешает операцию '{action}'"
            )
        return user
