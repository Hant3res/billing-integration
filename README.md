# Billing System — Система выставления счетов

Микросервисная система для управления тарифами, выставления счетов и обработки платежей.

## 🚀 Быстрый старт

### Предварительные требования
- Docker 20.10+
- Docker Compose 2.0+
- Git

### Запуск

```bash
# Клонировать репозиторий
git clone https://github.com/hant3res/billing-integration.git
cd billing-integration

# Запустить все сервисы
docker-compose up -d --build

# Проверить работу
curl http://localhost:5000/api/tariffs
Открыть в браузере
http://localhost:5000
📁 Структура проекта
billing-integration/
├── service_a_tariff.py      # Модуль А: тарифы и остатки
├── service_b_invoice.py     # Модуль Б: счета
├── service_c_payment.py     # Модуль В: платежи
├── orchestrator_service.py  # Оркестратор (Saga pattern)
├── index.html               # Фронтенд (Bootstrap)
├── docker-compose.yml       # Оркестрация контейнеров
├── Dockerfile.*             # Сборка образов
├── requirements.txt         # Python зависимости
├── tests/                   # Unit, интеграционные, E2E тесты
└── .github/workflows/ci.yml # CI/CD pipeline
🔌 API Endpoints
Tariff Service (порт 5001)
Метод	Endpoint	Описание
GET	/api/tariffs	Получить все тарифы
GET	/api/tariffs/{id}	Получить тариф по ID
POST	/api/tariffs	Создать тариф
POST	/api/tariffs/check_stock	Проверить остатки
POST	/api/tariffs/reserve	Зарезервировать
Invoice Service (порт 5002)
Метод	Endpoint	Описание
GET	/api/invoices	Получить все счета
POST	/api/invoices/create	Создать счет
PATCH	/api/invoices/{id}/pay	Отметить оплаченным
PATCH	/api/invoices/{id}/cancel	Отменить счет
Payment Service (порт 5003)
Метод	Endpoint	Описание
GET	/api/payments	Получить все платежи
POST	/api/payments/pay	Обработать платеж
GET	/api/payments/{id}	Получить платеж по ID
Orchestrator (порт 5000)
Метод	Endpoint	Описание
POST	/api/order/checkout	Оформить заказ
GET	/api/order/status/{id}	Статус заказа
GET	/	Фронтенд
📊 Примеры запросов
Оформление заказа
curl -X POST http://localhost:5000/api/order/checkout \
  -H "Content-Type: application/json" \
  -d '{"client_id": 100, "tariff_ids": [1, 4], "payment_method": "card"}'
Ответ (успех)

{
  "status": "success",
  "checkout_id": 1,
  "total_amount": 1500,
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000"
}
Ответ (ошибка — нет остатков)
{
  "error": "Stock check failed",
  "details": {
    "available": false,
    "unavailable": [
      {"id": 3, "name": "Extra Disk 10GB", "reason": "out of stock"}
    ]
  }
}
🧪 Тестирование
# Unit тесты
pytest tests/unit/ -v

# Интеграционные тесты
pytest tests/integration/ -v

# E2E тесты
pytest tests/e2e/ -v

# Ручное тестирование
python manual_test.py

# Бенчмарк производительности
python benchmark.py
📈 Производительность
Операция	Время (мс)
GET /api/tariffs (с кэшем)	~8-10
POST /api/order/checkout	~28
🐛 Устранение неисправностей
Ошибка подключения к БД
docker-compose exec mssql bash -c "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YourStrongPass123' -C -Q 'CREATE DATABASE billing_db'"
docker-compose restart
Очистка кэша Redis
docker-compose exec redis redis-cli FLUSHALL
📄 Лицензия
MIT

👨‍💻 Автор
hant3res

