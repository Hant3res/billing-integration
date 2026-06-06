#!/usr/bin/env python3
"""
Протокол ручного тестирования
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"
TARIFF_URL = "http://localhost:5001"

def test_1_get_tariffs():
    print("\n=== Тест 1: Получение списка тарифов ===")
    resp = requests.get(f"{TARIFF_URL}/api/tariffs")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Успех: получено {len(data['tariffs'])} тарифов")
        for t in data['tariffs']:
            print(f"   - {t['name']}: {t['price']} ₽ (остаток: {t['stock']})")
        return True
    else:
        print(f"❌ Ошибка: {resp.status_code}")
        return False

def test_2_successful_checkout():
    print("\n=== Тест 2: Успешное оформление заказа ===")
    payload = {"client_id": 100, "tariff_ids": [1, 4], "payment_method": "card"}
    resp = requests.post(f"{BASE_URL}/api/order/checkout", json=payload)
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Заказ оформлен: ID={data['checkout_id']}, Сумма={data['total_amount']} ₽")
        print(f"   Транзакция: {data['transaction_id']}")
        return True
    else:
        print(f"❌ Ошибка: {resp.status_code} - {resp.json()}")
        return False

def test_3_failed_checkout_out_of_stock():
    print("\n=== Тест 3: Ошибка при отсутствии остатков ===")
    payload = {"client_id": 100, "tariff_ids": [2], "payment_method": "card"}
    resp = requests.post(f"{BASE_URL}/api/order/checkout", json=payload)
    if resp.status_code != 200:
        print(f"✅ Ожидаемая ошибка: {resp.status_code}")
        print(f"   Детали: {resp.json()}")
        return True
    else:
        print(f"❌ Неожиданный успех: {resp.json()}")
        return False

def test_4_frontend_load():
    print("\n=== Тест 4: Загрузка фронтенда ===")
    resp = requests.get(f"{BASE_URL}/")
    if resp.status_code == 200:
        print(f"✅ Фронтенд загружен")
        return True
    else:
        print(f"❌ Ошибка: {resp.status_code}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("ПРОТОКОЛ РУЧНОГО ТЕСТИРОВАНИЯ")
    print("=" * 50)
    
    time.sleep(2)
    
    results = []
    results.append(("1. Получение тарифов", test_1_get_tariffs()))
    results.append(("2. Успешный checkout", test_2_successful_checkout()))
    results.append(("3. Ошибка при остатках", test_3_failed_checkout_out_of_stock()))
    results.append(("4. Загрузка фронтенда", test_4_frontend_load()))
    
    print("\n" + "=" * 50)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    print(f"\nВсего тестов: {total}, Пройдено: {passed}, Не пройдено: {total - passed}")
