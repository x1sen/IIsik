# Product Discovery Platform (ЛР № 3, ЛР № 4 и ЛР № 5)

Реализация распределённой системы управления продуктовыми гипотезами и исследованиями на базе архитектуры из ЛР № 1 и ЛР № 2 с системой безопасности на базе **Auth Service**, **JWT**, **Redis** и **RBAC**.

## Структура проекта

- **gateway/** — внешний слой GraphQL API (**FastAPI** + **Strawberry GraphQL**):
  - **app.py** — точка входа, извлечение **Authorization: Bearer** и подключение маршрутов **/graphql** и **/auth**;
  - **security.py** — проверка JWT, Redis-сессии и ролей (**require_auth**);
  - **types.py**, **resolvers.py**, **schema.py** — защищённые операции **Query** и **Mutation**, а также публичные **register**, **login**, **logout**;
  - **clients/interfaces.py**, **clients/mocks.py** — абстракции и mock-клиенты сервисов (включая **AuthClient**).
- **services/** — 12 доменных микросервисов с изолированными БД SQLite, координатор **business_operations.py** и **auth_service/** (**config.py**, **models.py**, **repository.py**, **seed.py**, **session_store.py**, **service.py**, **rest_api.py**).
- **shared/** — исключения (**EntityNotFoundError**, **ValidationError**, **BusinessRuleError**, **AuthenticationError**, **AuthorizationError**) и **db.py**.
- **tests/** — тесты сервисов, GraphQL API, бизнес-операций и безопасности (**test_security_auth.py**).

## Запуск

```bash
cd product_discovery_platform
python -m pip install -r requirements.txt
python -m pytest -v
python -m uvicorn gateway.app:app --reload
```

После запуска GraphiQL доступен по адресу http://127.0.0.1:8000/graphql.
