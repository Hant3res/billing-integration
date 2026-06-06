import pytest
import requests
import time

BASE_URL = "http://localhost:5000"
TARIFF_URL = "http://localhost:5001"

@pytest.fixture(scope="module")
def setup_tariffs():
    """Подготовка: убедиться, что есть тестовые тарифы"""
    resp = requests.get(f"{TARIFF_URL}/api/tariffs")
    tariffs = resp.json().get("tariffs", [])
    available = [t for t in tariffs if t.get("stock", 0) > 0]
    if len(available) < 2:
        pytest.skip("Not enough available tariffs for E2E test")
    return available[:2]

def test_e2e_full_checkout(setup_tariffs):
    """
    E2E тест: полный сценарий оформления заказа
    Клиент → просмотр тарифов → выбор → оформление → оплата
    """
    tariffs = setup_tariffs
    tariff_ids = [t["id"] for t in tariffs]
    
    print(f"\nE2E Test: Using tariffs {tariff_ids}")
    
    # Шаг 1: Получить тарифы (фронтенд)
    resp = requests.get(f"{BASE_URL}/api/tariffs")
    assert resp.status_code == 200
    tariffs_data = resp.json()
    assert "tariffs" in tariffs_data
    
    # Шаг 2: Оформить заказ
    payload = {
        "client_id": 999,
        "tariff_ids": tariff_ids,
        "payment_method": "card"
    }
    resp = requests.post(f"{BASE_URL}/api/order/checkout", json=payload, timeout=30)
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["status"] == "success"
    assert data["checkout_id"] is not None
    assert data["transaction_id"] is not None
    
    print(f"E2E Test passed: Order {data['checkout_id']}, Transaction {data['transaction_id']}")

def test_e2e_failed_checkout():
    """
    E2E тест: сценарий с ошибкой (нет остатков)
    """
    # Используем заведомо недоступный тариф (stock = 0)
    payload = {
        "client_id": 999,
        "tariff_ids": [3],
        "payment_method": "card"
    }
    resp = requests.post(f"{BASE_URL}/api/order/checkout", json=payload, timeout=30)
    # Должен вернуть ошибку
    assert resp.status_code != 200
    print(f"E2E Test failed scenario: {resp.status_code} - {resp.json()}")
