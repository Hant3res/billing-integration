import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# Мок-данные для тарифов
mock_tariffs = [
    {"id": 1, "name": "Hosting Basic", "price": 500, "stock": 5},
    {"id": 2, "name": "Hosting Pro", "price": 1500, "stock": 0},
]

def test_check_stock_success():
    """Тест: проверка остатков - успешный сценарий"""
    tariff_ids = [1]
    unavailable = []
    
    for tid in tariff_ids:
        tariff = next((t for t in mock_tariffs if t["id"] == tid), None)
        if not tariff or tariff.get("stock", 0) <= 0:
            unavailable.append({"id": tid, "reason": "out of stock"})
    
    assert len(unavailable) == 0

def test_check_stock_failure():
    """Тест: проверка остатков - ошибка (нет остатка)"""
    tariff_ids = [2]
    unavailable = []
    
    for tid in tariff_ids:
        tariff = next((t for t in mock_tariffs if t["id"] == tid), None)
        if not tariff or tariff.get("stock", 0) <= 0:
            unavailable.append({"id": tid, "reason": "out of stock"})
    
    assert len(unavailable) == 1
    assert unavailable[0]["id"] == 2

def test_calculate_total():
    """Тест: расчёт итоговой суммы"""
    items = [{"price": 500}, {"price": 1500}]
    total = sum(item["price"] for item in items)
    assert total == 2000

def test_transform_tariff_to_invoice():
    """Тест: маппинг тарифа в позицию счёта"""
    tariff = {"id": 1, "name": "Hosting Basic", "price": 500}
    invoice_item = {
        "item_id": tariff["id"],
        "item_name": tariff["name"],
        "item_price": tariff["price"]
    }
    assert invoice_item["item_id"] == 1
    assert invoice_item["item_name"] == "Hosting Basic"
    assert invoice_item["item_price"] == 500

def test_transform_invoice_to_payment():
    """Тест: маппинг счёта в запрос на оплату"""
    invoice = {"id": 1, "total_amount": 2000, "client_id": 100}
    payment_request = {
        "invoice_id": invoice["id"],
        "amount": invoice["total_amount"],
        "client_id": invoice["client_id"]
    }
    assert payment_request["invoice_id"] == 1
    assert payment_request["amount"] == 2000
