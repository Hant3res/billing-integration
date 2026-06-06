#!/usr/bin/env python3
"""
Регрессионное тестирование после исправлений
Проверяет, что старые сценарии продолжают работать
"""
import requests
import time

def test_successful_checkout():
    print("\n[Регрессия 1] Успешный checkout...")
    payload = {"client_id": 200, "tariff_ids": [1, 4], "payment_method": "card"}
    resp = requests.post("http://localhost:5000/api/order/checkout", json=payload, timeout=10)
    if resp.status_code == 200:
        print(f"   ✅ Успех: заказ {resp.json()['checkout_id']}")
        return True
    print(f"   ❌ Ошибка: {resp.status_code}")
    return False

def test_get_tariffs():
    print("\n[Регрессия 2] Получение тарифов...")
    resp = requests.get("http://localhost:5001/api/tariffs", timeout=5)
    if resp.status_code == 200:
        print(f"   ✅ Успех")
        return True
    print(f"   ❌ Ошибка: {resp.status_code}")
    return False

def test_frontend():
    print("\n[Регрессия 3] Загрузка фронтенда...")
    resp = requests.get("http://localhost:5000/", timeout=5)
    if resp.status_code == 200:
        print(f"   ✅ Успех")
        return True
    print(f"   ❌ Ошибка: {resp.status_code}")
    return False

if __name__ == "__main__":
    print("=" * 50)
    print("РЕГРЕССИОННОЕ ТЕСТИРОВАНИЕ")
    print("=" * 50)
    
    results = [
        test_get_tariffs(),
        test_frontend(),
        test_successful_checkout()
    ]
    
    print("\n" + "=" * 50)
    print("ИТОГИ РЕГРЕССИОННОГО ТЕСТИРОВАНИЯ")
    print("=" * 50)
    print(f"✅ Пройдено: {sum(results)} из {len(results)}")
    
    if all(results):
        print("✅ Все регрессионные тесты пройдены успешно!")
    else:
        print("❌ Некоторые регрессионные тесты не пройдены")
