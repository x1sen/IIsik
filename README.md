# Product Discovery Platform (ЛР № 7)

Устойчивая и оптимизированная распределённая система с механизмами **timeout** и **retry** для gRPC, обработкой ошибок и DLQ в **Kafka**, кешированием данных в **Redis** и централизованным логированием.

## Структура изменений

- **shared/resilience.py** — политика **RetryPolicy** (ограниченный retry для временных ошибок **UNAVAILABLE** / **DEADLINE_EXCEEDED**, **timeout** на каждый gRPC-вызов и преобразование кодов ошибок).
- **shared/cache.py** — клиент кеширования **RedisCache** (**get_json**, **set_json** с TTL, **invalidate_prefix** при событиях Kafka).
- **shared/logging_config.py** — структурированное логирование gRPC-вызовов, Kafka-сообщений, операций кеша и бизнес-сценариев.
- **gateway/clients/grpc_clients.py** — интеграция **_TimeoutInterceptor**, **execute_with_retry** и кеширования **RedisCache** для продуктов, метрик дашборда и сводки гипотез.
- **kafka_layer/producer.py**, **kafka_layer/consumer.py** — изоляция сбоев обработчиков в **dead_letter_queue** (DLQ) и инвалидация кеша в Redis.
- **tests/test_resilience_and_cache.py** — тесты **timeout**, **retry**, Redis-кеша, DLQ в Kafka, отката экспорта и логирования.

## Запуск

```bash
cd product_discovery_platform
python -m pip install -r requirements.txt
python -m pytest -v
python -m uvicorn gateway.app:app --reload
```

После запуска GraphiQL доступен по адресу http://127.0.0.1:8000/graphql.
