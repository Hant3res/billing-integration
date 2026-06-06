import requests
import logging
import json
from flask import Flask, request, jsonify
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Адреса сервисов
TARIFF_SERVICE_URL = "http://localhost:5001"
INVOICE_SERVICE_URL = "http://localhost:5002"
PAYMENT_SERVICE_URL = "http://localhost:5003"

# ========== Маппинг данных (функции-трансформеры) ==========
def map_tariff_to_invoice_item(tariff):
    """Маппинг: тариф -> позиция счёта"""
    return {
        "item_id": tariff.get("id"),
        "item_name": tariff.get("name"),
        "item_price": tariff.get("price"),
        "currency": tariff.get("currency")
    }

def map_invoice_to_payment_request(invoice):
    """Маппинг: счёт -> запрос на оплату"""
    return {
        "invoice_id": invoice.get("id"),
        "amount": invoice.get("total_amount"),
        "currency": invoice.get("currency"),
        "client_id": invoice.get("client_id")
    }

def map_payment_response_to_result(payment_response):
    """Маппинг: ответ платежей -> итоговый результат"""
    return {
        "success": payment_response.get("status") == "completed",
        "transaction_id": payment_response.get("transaction_id"),
        "message": payment_response.get("message")
    }

# ========== Основной сценарий: создание счёта и оплата ==========
@app.route('/api/order/checkout', methods=['POST'])
def checkout():
    """
    Оркестрация процесса:
    1. Получить выбранные тарифы
    2. Создать счёт
    3. Оплатить счёт
    """
    data = request.get_json()
    client_id = data.get('client_id')
    tariff_ids = data.get('tariff_ids', [])
    
    if not client_id or not tariff_ids:
        return jsonify({"error": "client_id and tariff_ids required"}), 400
    
    logger.info(f"Starting checkout for client {client_id}, tariffs: {tariff_ids}")
    
    # Шаг 1: Получить тарифы из Модуля А
    tariffs = []
    for tariff_id in tariff_ids:
        try:
            resp = requests.get(f"{TARIFF_SERVICE_URL}/api/tariffs/{tariff_id}")
            if resp.status_code == 200:
                tariff = resp.json()
                tariffs.append(tariff)
                logger.info(f"Fetched tariff {tariff_id}: {tariff.get('name')}")
            else:
                logger.error(f"Tariff {tariff_id} not found")
                return jsonify({"error": f"Tariff {tariff_id} not found"}), 404
        except Exception as e:
            logger.error(f"Error calling Tariff Service: {e}")
            return jsonify({"error": "Tariff service unavailable"}), 503
    
    # Маппинг: тарифы -> позиции для счёта
    invoice_items = [map_tariff_to_invoice_item(t) for t in tariffs]
    
    # Шаг 2: Создать счёт в Модуле Б
    try:
        invoice_payload = {
            "client_id": client_id,
            "tariff_ids": tariff_ids
        }
        resp = requests.post(
            f"{INVOICE_SERVICE_URL}/api/invoices/create",
            json=invoice_payload,
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code != 201:
            logger.error(f"Invoice creation failed: {resp.status_code}")
            return jsonify({"error": "Invoice creation failed"}), 500
        
        invoice = resp.json()
        logger.info(f"Invoice created with id {invoice.get('id')}, amount {invoice.get('total_amount')}")
    except Exception as e:
        logger.error(f"Error calling Invoice Service: {e}")
        return jsonify({"error": "Invoice service unavailable"}), 503
    
    # Шаг 3: Оплатить счёт в Модуле В
    try:
        payment_payload = {
            "invoice_id": invoice.get("id"),
            "payment_method": data.get("payment_method", "card")
        }
        resp = requests.post(
            f"{PAYMENT_SERVICE_URL}/api/payments/pay",
            json=payment_payload,
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code != 200:
            logger.error(f"Payment failed: {resp.status_code}")
            return jsonify({"error": "Payment failed"}), 500
        
        payment_result = resp.json()
        result = map_payment_response_to_result(payment_result)
        logger.info(f"Payment completed: transaction {result.get('transaction_id')}")
    except Exception as e:
        logger.error(f"Error calling Payment Service: {e}")
        return jsonify({"error": "Payment service unavailable"}), 503
    
    # Возвращаем итоговый результат
    response = {
        "checkout_id": invoice.get("id"),
        "client_id": client_id,
        "items": invoice_items,
        "total_amount": invoice.get("total_amount"),
        "payment": result,
        "status": "completed",
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Checkout completed successfully for client {client_id}")
    return jsonify(response), 200

@app.route('/api/order/status/<int:invoice_id>', methods=['GET'])
def get_order_status(invoice_id):
    """Получить статус заказа (счёта)"""
    try:
        resp = requests.get(f"{INVOICE_SERVICE_URL}/api/invoices")
        if resp.status_code != 200:
            return jsonify({"error": "Invoice service unavailable"}), 503
        
        invoices = resp.json().get('invoices', [])
        invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)
        
        if not invoice:
            return jsonify({"error": "Invoice not found"}), 404
        
        return jsonify({
            "invoice_id": invoice_id,
            "status": invoice.get("status"),
            "total_amount": invoice.get("total_amount")
        }), 200
    except Exception as e:
        logger.error(f"Error getting order status: {e}")
        return jsonify({"error": "Service unavailable"}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
