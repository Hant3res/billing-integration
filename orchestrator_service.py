import requests
import logging
import os
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

TARIFF_URL = "http://tariff-service:5001"
INVOICE_URL = "http://invoice-service:5002"
PAYMENT_URL = "http://payment-service:5003"

# Путь к папке с HTML файлами (текущая директория)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def serve_index():
    """Главная страница"""
    html_path = os.path.join(BASE_DIR, 'index.html')
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    return "index.html not found", 404

@app.route('/api/order/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    client_id = data.get('client_id')
    tariff_ids = data.get('tariff_ids', [])
    payment_method = data.get('payment_method', 'card')
    
    if not client_id or not tariff_ids:
        return jsonify({"error": "client_id and tariff_ids required"}), 400
    
    logger.info(f"Starting checkout for client {client_id}, tariffs: {tariff_ids}")
    
    # ШАГ 1: Проверка остатков
    try:
        resp = requests.post(f"{TARIFF_URL}/api/tariffs/check_stock", 
                            json={"tariff_ids": tariff_ids})
        if resp.status_code != 200:
            logger.error(f"Stock check failed: {resp.json()}")
            return jsonify({"error": "Stock check failed", "details": resp.json()}), 400
        logger.info("Stock check passed")
    except Exception as e:
        logger.error(f"Stock check error: {e}")
        return jsonify({"error": "Stock service unavailable"}), 503
    
    # ШАГ 2: Резервирование тарифов
    try:
        resp = requests.post(f"{TARIFF_URL}/api/tariffs/reserve", 
                            json={"tariff_ids": tariff_ids})
        if resp.status_code != 200:
            logger.error(f"Reservation failed")
            return jsonify({"error": "Reservation failed"}), 400
        logger.info("Tariffs reserved")
    except Exception as e:
        logger.error(f"Reservation error: {e}")
        return jsonify({"error": "Reservation service unavailable"}), 503
    
    # ШАГ 3: Создание счёта
    try:
        resp = requests.post(f"{INVOICE_URL}/api/invoices/create",
                            json={"client_id": client_id, "tariff_ids": tariff_ids})
        if resp.status_code != 201:
            logger.error(f"Invoice creation failed")
            compensate_reservation(tariff_ids)
            return jsonify({"error": "Invoice creation failed"}), 500
        invoice = resp.json()
        invoice_id = invoice.get('id')
        logger.info(f"Invoice created: {invoice_id}")
    except Exception as e:
        logger.error(f"Invoice error: {e}")
        compensate_reservation(tariff_ids)
        return jsonify({"error": "Invoice service unavailable"}), 503
    
    # ШАГ 4: Оплата
    try:
        resp = requests.post(f"{PAYMENT_URL}/api/payments/pay",
                            json={"invoice_id": invoice_id, "payment_method": payment_method})
        if resp.status_code != 200:
            logger.error(f"Payment failed")
            compensate_invoice(invoice_id)
            compensate_reservation(tariff_ids)
            return jsonify({"error": "Payment failed", "details": resp.json()}), 400
        payment = resp.json()
        logger.info(f"Payment completed: {payment.get('transaction_id')}")
    except Exception as e:
        logger.error(f"Payment error: {e}")
        compensate_invoice(invoice_id)
        compensate_reservation(tariff_ids)
        return jsonify({"error": "Payment service unavailable"}), 503
    
    return jsonify({
        "status": "success",
        "checkout_id": invoice_id,
        "client_id": client_id,
        "total_amount": invoice.get('total_amount'),
        "transaction_id": payment.get('transaction_id'),
        "timestamp": datetime.now().isoformat()
    }), 200

def compensate_reservation(tariff_ids):
    try:
        logger.info(f"Compensating reservation for tariffs: {tariff_ids}")
    except Exception as e:
        logger.error(f"Compensation failed: {e}")

def compensate_invoice(invoice_id):
    try:
        requests.patch(f"{INVOICE_URL}/api/invoices/{invoice_id}/cancel", timeout=2)
        logger.info(f"Invoice {invoice_id} cancelled")
    except Exception as e:
        logger.error(f"Invoice cancellation failed: {e}")

@app.route('/api/order/status/<int:invoice_id>', methods=['GET'])
def get_status(invoice_id):
    try:
        resp = requests.get(f"{INVOICE_URL}/api/invoices")
        invoices = resp.json().get('invoices', [])
        invoice = next((i for i in invoices if i['id'] == invoice_id), None)
        if invoice:
            return jsonify(invoice), 200
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 503

@app.route('/api/tariffs', methods=['GET'])
def proxy_tariffs():
    """Прокси для получения тарифов с фронтенда"""
    try:
        resp = requests.get(f"{TARIFF_URL}/api/tariffs")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
