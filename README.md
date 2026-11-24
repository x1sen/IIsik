# Product Discovery Platform (ЛР № 6)

Интегрированная распределённая система с межсервисным взаимодействием на базе **gRPC** (**protobuf**) и событийным обменом через **Apache Kafka** (**Producer** и **Consumer**).

## Структура проекта

- **protos/** — protobuf-контракты (**platform.proto**) и сгенерированные модули (**platform_pb2.py**, **platform_pb2_grpc.py**) для всех 13 сервисов.
- **grpc_layer/** — gRPC-серверы внутренних сервисов (**server.py**) и конвертеры protobuf-сообщений (**converters.py**).
- **kafka_layer/** — конверт событий и топики (**events.py**), **KafkaEventProducer** (**producer.py**) и **KafkaEventConsumer** с обработчиками для **AnalyticsService**, **RoadmapService**, **NotificationService** и **AuditService** (**consumer.py**).
- **gateway/clients/** — абстрактные интерфейсы (**interfaces.py**) и реальные gRPC-клиенты (**grpc_clients.py**), заменившие mock-заглушки.
- **services/** — внутренние микросервисы с изолированными БД SQLite и координатор сквозных сценариев **business_operations.py**, использующий gRPC и публикацию событий в Kafka.
- **tests/** — тесты gRPC-вызовов и событийного взаимодействия через Kafka (**test_grpc_and_kafka.py**).

## Запуск

```bash
cd product_discovery_platform
python -m pip install -r requirements.txt
python -m pytest -v
python -m uvicorn gateway.app:app --reload
```

После запуска GraphiQL доступен по адресу http://127.0.0.1:8000/graphql.
