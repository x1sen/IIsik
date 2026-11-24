# Product Discovery Platform (ЛР № 3 и ЛР № 4)

Реализация распределённой системы управления продуктовыми гипотезами и исследованиями на базе архитектуры из ЛР № 1 и ЛР № 2.

## Структура проекта

- **gateway/** — внешний слой GraphQL API (**FastAPI** + **Strawberry GraphQL**):
  - **config.py** — конфигурация шлюза;
  - **types.py** — GraphQL **type**, **enum**, **input** и вложенные резолверы;
  - **resolvers.py** — тонкие резолверы **Query** и **Mutation** (без бизнес-логики);
  - **schema.py** — корневая схема **Query** и **Mutation**;
  - **clients/interfaces.py** — абстрактные интерфейсы клиентов сервисов;
  - **clients/mocks.py** — mock-реализации клиентов (без реальных сетевых gRPC-вызовов).
- **services/** — 12 изолированных микросервисов (**hypothesis_service**, **research_service**, **report_service**, **roadmap_service**, **analytics_service**, **product_service**, **user_service**, **notification_service**, **idea_portal_service**, **file_storage_service**, **audit_service**, **integration_service**), каждый со своей БД SQLite и слоями **config.py**, **models.py**, **repository.py**, **service.py**, **seed.py**, а также координатор сквозных сценариев **business_operations.py**.
- **shared/** — общие исключения (**EntityNotFoundError**, **ValidationError**, **BusinessRuleError**) и помощник подключения к SQLite.
- **tests/** — модульные и интеграционные тесты сервисов и GraphQL API.

## Запуск

```bash
cd product_discovery_platform
python -m pip install -r requirements.txt
python -m pytest -v
python -m uvicorn gateway.app:app --reload
```

После запуска GraphiQL доступен по адресу http://127.0.0.1:8000/graphql.
