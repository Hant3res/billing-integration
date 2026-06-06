import requests
import logging
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError

# Настройка логирования
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, 'client_id'):
            log_entry['client_id'] = record.client_id
        return json.dumps(log_entry)

logger = logging.getLogger("orchestrator")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

app = Flask(__name__)

TARIFF_URL = "http://tariff-service:5001"
INVOICE_URL = "http://invoice-service:5002"
PAYMENT_URL = "http://payment-service:5003"

def retry_policy():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout))
    )

@retry_policy()
def call_with_retry(url, method='GET', json_data=None, timeout=5):
    if method == 'GET':
        resp = requests.get(url, timeout=timeout)
    else:
        resp = requests.post(url, json=json_data, timeout=timeout)
    resp.raise_for_status()
    return resp

@app.route('/')
def serve_index():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except:
        return "index.html not found", 404

@app.route('/api/order/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    client_id = data.get('client_id')
    tariff_ids = data.get('tariff_ids', [])
    payment_method = data.get('payment_method', 'card')

    logger.info("Checkout started", extra={'client_id': client_id})

    if not client_id or not tariff_ids:
        return jsonify({"error": "client_id and tariff_ids required"}), 400

    # Шаг 1: Проверка остатков
    try:
        resp = requests.post(f"{TARIFF_URL}/api/tariffs/check_stock", json={"tariff_ids": tariff_ids}, timeout=5)
        if resp.status_code != 200:
            logger.error(f"Stock check failed: {resp.json()}")
            return jsonify({"error": "Stock check failed", "details": resp.json()}), 400
    except Exception as e:
        logger.error(f"Stock check error: {e}")
        return jsonify({"error": "Stock service unavailable"}), 503

    # Шаг 2: Резервирование
    try:
        resp = requests.post(f"{TARIFF_URL}/api/tariffs/reserve", json={"tariff_ids": tariff_ids}, timeout=5)
        if resp.status_code != 200:
            return jsonify({"error": "Reservation failed"}), 400
    except Exception as e:
        return jsonify({"error": "Reservation service unavailable"}), 503

    # Шаг 3: Создание счёта
    try:
        resp = call_with_retry(f"{INVOICE_URL}/api/invoices/create", 'POST', {"client_id": client_id, "tariff_ids": tariff_ids})
        invoice = resp.json()
        invoice_id = invoice.get('id')
    except RetryError:
        return jsonify({"error": "Invoice service unavailable"}), 503

    # Шаг 4: Оплата
    try:
        resp = call_with_retry(f"{PAYMENT_URL}/api/payments/pay", 'POST', {"invoice_id": invoice_id, "payment_method": payment_method})
        payment = resp.json()
    except RetryError:
        return jsonify({"error": "Payment service unavailable"}), 503

    logger.info("Checkout completed", extra={'client_id': client_id, 'invoice_id': invoice_id})
    return jsonify({
        "status": "success",
        "checkout_id": invoice_id,
        "total_amount": invoice.get('total_amount'),
        "transaction_id": payment.get('transaction_id')
    }), 200

@app.route('/api/tariffs', methods=['GET'])
def proxy_tariffs():
    try:
        resp = call_with_retry(f"{TARIFF_URL}/api/tariffs", 'GET')
        return jsonify(resp.json()), 200
    except RetryError:
        return jsonify({"error": "Tariff service unavailable"}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
