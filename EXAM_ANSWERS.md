# Ответы на контрольные вопросы

## 1. Какие стили интеграции использованы и почему?

**Ответ:** Использованы два стиля:
- **Синхронный (REST API)** — для прямых запросов между модулями (проверка остатков, создание счета, оплата). Выбран из-за простоты реализации и мгновенной обратной связи.
- **Асинхронный (вебхуки)** — для уведомлений между сервисами. Используется для передачи информации о создании тарифа из модуля А в модуль Б.

## 2. Покажите BPMN диаграмму. Как она реализована в коде?

**BPMN процесс:**
Старт → Выбор тарифов → Оформление заказа → Проверка остатков → [достаточно?] → Резервирование → Создание счета → Оплата → [успех?] → Завершение

**Реализация в коде:** `orchestrator_service.py` — функция `checkout()`:
```python
@app.route('/api/order/checkout', methods=['POST'])
def checkout():
    # 1. Проверка остатков
    resp = call_with_retry(f"{TARIFF_URL}/api/tariffs/check_stock", 'POST', {...})
    # 2. Резервирование
    resp = call_with_retry(f"{TARIFF_URL}/api/tariffs/reserve", 'POST', {...})
    # 3. Создание счета
    resp = call_with_retry(f"{INVOICE_URL}/api/invoices/create", 'POST', {...})
    # 4. Оплата
    resp = call_with_retry(f"{PAYMENT_URL}/api/payments/pay", 'POST', {...})
3. Как вы настраивали Web API для каждого модуля?
Ответ: Каждый модуль — это Flask приложение:
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/api/tariffs', methods=['GET'])
def get_tariffs():
    return jsonify({"tariffs": tariffs})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
Каждый сервис запускается на своём порту (5001-5003) и упакован в Docker.

4. Что такое Swagger/OpenAPI и как он генерируется?
Ответ: OpenAPI — спецификация для описания REST API. Swagger — инструмент для визуализации.
В проекте используется swagger.yaml — ручное описание всех эндпоинтов, форматов запросов и ответов.

5. Как вы обеспечивали транзакционность между модулями (Saga)?
Ответ: Использован паттерн Saga с компенсациями:
try:
    invoice = create_invoice()
    payment = process_payment()
except Exception:
    compensate_invoice(invoice_id)   # Отмена счета
    compensate_reservation(tariff_ids) # Возврат остатков
При ошибке на любом шаге вызываются компенсирующие действия.

6. Покажите UML диаграмму последовательности. Какие методы ей соответствуют?
Диаграмма: uml_sequence_updated.puml
Соответствие в коде:

Клиент → POST /api/order/checkout

Оркестратор → POST /api/tariffs/check_stock

Оркестратор → POST /api/invoices/create

Оркестратор → POST /api/payments/pay

7. Как GitHub Actions собирает и тестирует проекты?
Ответ: .github/workflows/ci.yml:
jobs:
  test:
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Run unit tests
        run: pytest tests/unit/ -v
      - name: Start Docker services
        run: docker-compose up -d --build
      - name: Run integration tests
        run: pytest tests/integration/ -v
8. Как обрабатывается ошибка при недоступности модуля оплаты (Polly)?
Ответ: Использована библиотека Tenacity (аналог Polly):
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
def call_with_retry(url, method='GET', json_data=None):
    resp = requests.post(url, json=json_data, timeout=5)
    resp.raise_for_status()
    return resp
При недоступности сервиса — 3 попытки с экспоненциальной задержкой.

9. Как вы логируете? Покажите пример лога.
Ответ: Структурированное логирование в JSON:
class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "client_id": getattr(record, 'client_id', None)
        })
Пример лога:
{"timestamp": "2026-06-06T04:00:00.000", "level": "INFO", "message": "Checkout started", "client_id": 100}
10. Какие метрики производительности улучшились?
Ответ:

Операция	До	После
GET /tariffs	200-300 мс	8-10 мс (20-30x)
POST /checkout	400-500 мс	28 мс (14-18x)
За счёт: Redis кэширование, инвалидация кэша, параллельные вызовы.

11. Как вы тестировали интеграцию?
Ответ:

Unit тесты: tests/unit/test_adapters.py (без внешних зависимостей)

Интеграционные: tests/integration/test_api.py (реальные запросы к API)

E2E тесты: tests/e2e/test_end_to_end.py (полный сценарий клиент → БД)

12. Что такое Entity Framework Core? Как использовали миграции?
Ответ: В проекте используется SQLAlchemy (аналог EF Core для Python):
class Tariff(db.Model):
    __tablename__ = 'tariffs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

with app.app_context():
    db.create_all()  # Автоматическое создание таблиц
13. Как настроен docker-compose?
Ответ: docker-compose.yml описывает 6 сервисов:
services:
  mssql:      # БД
  redis:      # Кэш
  tariff-service:
  invoice-service:
  payment-service:
  orchestrator-service:
Каждый сервис имеет свой Dockerfile, порты и переменные окружения.

14. Как бы вы добавили новый модуль (например, «Склад»)?
Ответ:

Создать новый сервис stock_service.py на Flask

Добавить эндпоинты: GET /api/stock, POST /api/stock/reserve

Добавить сервис в docker-compose.yml

В оркестраторе добавить вызовы нового сервиса

Добавить компенсации при ошибках

15. В чем разница синхронного и асинхронного взаимодействия?
Ответ:

Характеристика	Синхронное (REST)	Асинхронное (RabbitMQ)
Ожидание ответа	Да (блокирующее)	Нет
Задержка	Низкая	Выше (очередь)
Надёжность	Ниже (timeout)	Выше (persistent queue)
Сценарии	Запрос-ответ	События, уведомления
В проекте используется синхронный REST для прямых вызовов и вебхуки для асинхронных уведомлений.

