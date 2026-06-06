# Проверка развертывания

## Запуск системы
```bash
docker-compose up -d --build
Ожидаемые контейнеры
Контейнер	Статус	Порт
billing-integration-mssql-1	Up	1433
billing-integration-redis-1	Up	6379
billing-integration-tariff-service-1	Up	5001
billing-integration-invoice-service-1	Up	5002
billing-integration-payment-service-1	Up	5003
billing-integration-orchestrator-service-1	Up	5000
Проверка работоспособности
# Проверка тарифов
curl http://localhost:5001/api/tariffs

# Проверка фронтенда
curl http://localhost:5000/

# Сквозной сценарий
curl -X POST http://localhost:5000/api/order/checkout \
  -H "Content-Type: application/json" \
  -d '{"client_id": 100, "tariff_ids": [1, 4], "payment_method": "card"}'
Остановка системы
docker-compose down
