from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import redis
import json
import time

app = Flask(__name__)

# Подключение к Redis
redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'), decode_responses=True)

DATABASE_URL = os.getenv('DATABASE_URL', 'mssql+pyodbc://sa:YourStrongPass123@mssql:1433/billing_db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Tariff(db.Model):
    __tablename__ = 'tariffs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='RUB')
    stock = db.Column(db.Integer, default=10)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "currency": self.currency,
            "stock": self.stock
        }

with app.app_context():
    db.create_all()
    if Tariff.query.count() == 0:
        test_data = [
            Tariff(name="Hosting Basic", price=500, stock=5),
            Tariff(name="Hosting Pro", price=1500, stock=3),
            Tariff(name="Extra Disk 10GB", price=300, stock=0),
            Tariff(name="SSL Certificate", price=1000, stock=10),
        ]
        for t in test_data:
            db.session.add(t)
        db.session.commit()
        # Очистить кэш при добавлении данных
        redis_client.delete('tariffs')
        print("Test data inserted")

@app.route('/api/tariffs', methods=['GET'])
def get_tariffs():
    start_time = time.time()
    
    # Пытаемся получить из кэша
    cached = redis_client.get('tariffs')
    if cached:
        elapsed = (time.time() - start_time) * 1000
        print(f"[CACHE HIT] Response time: {elapsed:.2f}ms")
        return jsonify(json.loads(cached)), 200
    
    # Если нет в кэше - запрос в БД
    tariffs = Tariff.query.all()
    result = {"tariffs": [t.to_dict() for t in tariffs]}
    
    # Сохраняем в кэш на 5 минут
    redis_client.setex('tariffs', 300, json.dumps(result))
    
    elapsed = (time.time() - start_time) * 1000
    print(f"[CACHE MISS] DB query time: {elapsed:.2f}ms")
    
    return jsonify(result), 200

@app.route('/api/tariffs/<int:tariff_id>', methods=['GET'])
def get_tariff(tariff_id):
    tariff = db.session.get(Tariff, tariff_id)
    if tariff:
        return jsonify(tariff.to_dict()), 200
    return jsonify({"error": "Not found"}), 404

@app.route('/api/tariffs/check_stock', methods=['POST'])
def check_stock():
    data = request.get_json()
    tariff_ids = data.get('tariff_ids', [])
    
    unavailable = []
    for tid in tariff_ids:
        tariff = db.session.get(Tariff, tid)
        if not tariff:
            unavailable.append({"id": tid, "reason": "not found"})
        elif tariff.stock <= 0:
            unavailable.append({"id": tid, "name": tariff.name, "reason": "out of stock"})
    
    if unavailable:
        return jsonify({"available": False, "unavailable": unavailable}), 400
    return jsonify({"available": True}), 200

@app.route('/api/tariffs/reserve', methods=['POST'])
def reserve_stock():
    data = request.get_json()
    tariff_ids = data.get('tariff_ids', [])
    
    for tid in tariff_ids:
        tariff = db.session.get(Tariff, tid)
        if tariff and tariff.stock > 0:
            tariff.stock -= 1
    db.session.commit()
    
    # Инвалидируем кэш после изменения данных
    redis_client.delete('tariffs')
    
    return jsonify({"reserved": True, "tariff_ids": tariff_ids}), 200

@app.route('/api/tariffs/clear_cache', methods=['POST'])
def clear_cache():
    redis_client.delete('tariffs')
    return jsonify({"status": "cache cleared"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
