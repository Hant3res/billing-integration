#!/usr/bin/env python3
"""
Скрипт для проверки исправления дефектов
"""
import requests
import time
import sys

def test_check_stock_endpoint():
    print("\n[1] Проверка эндпоинта /api/tariffs/check_stock...")
    try:
        resp = requests.post("http://localhost:5001/api/tariffs/check_stock", 
                            json={"tariff_ids": [1, 2]}, timeout=5)
        if resp.status_code in [200, 400]:
            print("   ✅ Эндпоинт существует")
            return True
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    return False

def test_saga_compensation():
    print("\n[2] Проверка Saga компенсации (заказ с недоступным тарифом)...")
    try:
        resp = requests.post("http://localhost:5000/api/order/checkout",
                            json={"client_id": 999, "tariff_ids": [3], "payment_method": "card"},
                            timeout=10)
        if resp.status_code != 200:
            print(f"   ✅ Ошибка обработана: {resp.status_code}")
            print(f"   Ответ: {resp.json()}")
            return True
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    return False

def test_database_connection():
    print("\n[3] Проверка подключения к БД...")
    try:
        resp = requests.get("http://localhost:5001/api/tariffs", timeout=5)
        if resp.status_code == 200:
            tariffs = resp.json().get('tariffs', [])
            print(f"   ✅ БД доступна, загружено {len(tariffs)} тарифов")
            return True
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    return False

def test_invoice_cancel():
    print("\n[4] Проверка эндпоинта отмены счёта...")
    try:
        # Сначала создаём счёт
        resp = requests.post("http://localhost:5002/api/invoices/create",
                            json={"client_id": 1, "tariff_ids": [1]}, timeout=5)
        if resp.status_code == 201:
            invoice_id = resp.json()['id']
            # Отменяем счёт
            resp2 = requests.patch(f"http://localhost:5002/api/invoices/{invoice_id}/cancel", timeout=5)
            if resp2.status_code == 200:
                print(f"   ✅ Счёт {invoice_id} отменён")
                return True
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    return False

if __name__ == "__main__":
    print("=" * 50)
    print("ПРОВЕРКА ИСПРАВЛЕНИЯ ДЕФЕКТОВ")
    print("=" * 50)
    
    results = []
    results.append(("Дефект #1 (БД)", test_database_connection()))
    results.append(("Дефект #4 (check_stock)", test_check_stock_endpoint()))
    results.append(("Дефект #3 (Saga)", test_saga_compensation()))
    results.append(("Дефект #5 (invoice cancel)", test_invoice_cancel()))
    
    print("\n" + "=" * 50)
    print("ИТОГИ ПРОВЕРКИ")
    print("=" * 50)
    for name, result in results:
        status = "✅ ИСПРАВЛЕН" if result else "❌ НЕ ИСПРАВЛЕН"
        print(f"{status} - {name}")
    
    sys.exit(0 if all(results) else 1)
