import pytest
import requests
import time

BASE_URL = "http://localhost:5000"
TARIFF_URL = "http://localhost:5001"
INVOICE_URL = "http://localhost:5002"
PAYMENT_URL = "http://localhost:5003"

@pytest.fixture(scope="module")
def wait_for_services():
    """Ожидание готовности сервисов"""
    max_retries = 30
    for i in range(max_retries):
        try:
            resp = requests.get(f"{TARIFF_URL}/api/tariffs", timeout=2)
            if resp.status_code == 200:
                print("Services are ready")
                return
        except:
            pass
        time.sleep(1)
    pytest.fail("Services not ready")

def test_get_tariffs(wait_for_services):
    """Интеграционный тест: получение списка тарифов"""
    resp = requests.get(f"{TARIFF_URL}/api/tariffs")
    assert resp.status_code == 200
    data = resp.json()
    assert "tariffs" in data
    assert len(data["tariffs"]) > 0

def test_create_invoice(wait_for_services):
    """Интеграционный тест: создание счёта"""
    payload = {"client_id": 100, "tariff_ids": [1, 4]}
    resp = requests.post(f"{INVOICE_URL}/api/invoices/create", json=payload)
    assert resp.status_code == 201
    invoice = resp.json()
    assert invoice["client_id"] == 100
    assert invoice["status"] == "pending"

def test_checkout_success(wait_for_services):
    """Интеграционный тест: успешный checkout"""
    payload = {"client_id": 100, "tariff_ids": [1, 4], "payment_method": "card"}
    resp = requests.post(f"{BASE_URL}/api/order/checkout", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "checkout_id" in data
    assert "transaction_id" in data

def test_checkout_stock_error(wait_for_services):
    """Интеграционный тест: ошибка при недостатке остатков"""
    payload = {"client_id": 100, "tariff_ids": [2], "payment_method": "card"}
    resp = requests.post(f"{BASE_URL}/api/order/checkout", json=payload)
    # Может вернуть 400 или 503 в зависимости от состояния
    assert resp.status_code in [400, 503]
