#!/usr/bin/env python3
"""
Замер производительности (до и после оптимизации)
"""
import requests
import time
import statistics

BASE_URL = "http://localhost:5000"
TARIFF_URL = "http://localhost:5001"

def measure_time(func, name, iterations=10):
    """Замер времени выполнения"""
    times = []
    print(f"\n📊 Замер: {name}")
    
    for i in range(iterations):
        start = time.time()
        result = func()
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        status = "✅" if result else "❌"
        print(f"   {status} Попытка {i+1}: {elapsed:.2f}ms")
    
    avg = statistics.mean(times)
    min_t = min(times)
    max_t = max(times)
    
    print(f"   📈 Среднее: {avg:.2f}ms | Мин: {min_t:.2f}ms | Макс: {max_t:.2f}ms")
    return avg

def test_get_tariffs():
    """Тест: получение списка тарифов"""
    try:
        resp = requests.get(f"{TARIFF_URL}/api/tariffs", timeout=10)
        return resp.status_code == 200
    except:
        return False

def test_checkout():
    """Тест: оформление заказа"""
    try:
        payload = {"client_id": 100, "tariff_ids": [1, 4], "payment_method": "card"}
        resp = requests.post(f"{BASE_URL}/api/order/checkout", json=payload, timeout=30)
        return resp.status_code == 200
    except:
        return False

def clear_cache():
    """Очистка кэша тарифов"""
    try:
        requests.post(f"{TARIFF_URL}/api/tariffs/clear_cache", timeout=5)
        return True
    except:
        return False

def warmup_cache():
    """Прогрев кэша"""
    requests.get(f"{TARIFF_URL}/api/tariffs", timeout=10)
    time.sleep(1)

if __name__ == "__main__":
    print("=" * 60)
    print("ЗАМЕР ПРОИЗВОДИТЕЛЬНОСТИ ИНТЕГРАЦИИ")
    print("=" * 60)
    
    print("\n🔧 Подготовка: очистка кэша...")
    clear_cache()
    
    # Замер без кэша (первый запрос)
    print("\n" + "=" * 60)
    print("📉 ЗАМЕР 1: БЕЗ КЭША (CACHE MISS)")
    print("=" * 60)
    time_without_cache = measure_time(test_get_tariffs, "Получение тарифов (без кэша)")
    
    # Замер с кэшем (повторный запрос)
    print("\n" + "=" * 60)
    print("📈 ЗАМЕР 2: С КЭШЕМ (CACHE HIT)")
    print("=" * 60)
    time_with_cache = measure_time(test_get_tariffs, "Получение тарифов (с кэшем)")
    
    # Замер сквозного сценария
    print("\n" + "=" * 60)
    print("🔄 ЗАМЕР 3: СКВОЗНОЙ СЦЕНАРИЙ (CHECKOUT)")
    print("=" * 60)
    time_checkout = measure_time(test_checkout, "Оформление заказа")
    
    print("\n" + "=" * 60)
    print("📊 СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ")
    print("=" * 60)
    print(f"| Операция                    | Время (ms) |")
    print(f"|----------------------------|------------|")
    print(f"| GET /api/tariffs (без кэша) | {time_without_cache:10.2f} |")
    print(f"| GET /api/tariffs (с кэшем)  | {time_with_cache:10.2f} |")
    print(f"| POST /api/order/checkout    | {time_checkout:10.2f} |")
    
    if time_without_cache > 0:
        speedup = time_without_cache / time_with_cache if time_with_cache > 0 else 0
        print(f"\n🚀 Ускорение кэширования: ~{speedup:.1f}x")
    
    print("\n✅ Замеры завершены")
