from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import requests

app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'mssql+pyodbc://sa:YourStrongPass123@localhost:1433/billing_db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Tariff(db.Model):
    __tablename__ = 'tariffs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='RUB')
    stock = db.Column(db.Integer, default=10)  # остатки (сколько доступно)

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
            Tariff(name="Extra Disk 10GB", price=300, stock=0),  # нет в наличии
            Tariff(name="SSL Certificate", price=1000, stock=10),
        ]
        for t in test_data:
            db.session.add(t)
        db.session.commit()
        print("Test data inserted")

@app.route('/api/tariffs', methods=['GET'])
def get_tariffs():
    tariffs = Tariff.query.all()
    return jsonify({"tariffs": [t.to_dict() for t in tariffs]}), 200

@app.route('/api/tariffs/<int:tariff_id>', methods=['GET'])
def get_tariff(tariff_id):
    tariff = Tariff.query.get(tariff_id)
    if tariff:
        return jsonify(tariff.to_dict()), 200
    return jsonify({"error": "Not found"}), 404

@app.route('/api/tariffs/check_stock', methods=['POST'])
def check_stock():
    """Проверка остатков: {'tariff_ids': [1,2,3]}"""
    data = request.get_json()
    tariff_ids = data.get('tariff_ids', [])
    
    unavailable = []
    for tid in tariff_ids:
        tariff = Tariff.query.get(tid)
        if not tariff:
            unavailable.append({"id": tid, "reason": "not found"})
        elif tariff.stock <= 0:
            unavailable.append({"id": tid, "name": tariff.name, "reason": "out of stock"})
        elif tariff.stock < data.get('quantities', {}).get(str(tid), 1):
            unavailable.append({"id": tid, "name": tariff.name, "reason": "insufficient stock"})
    
    if unavailable:
        return jsonify({"available": False, "unavailable": unavailable}), 400
    return jsonify({"available": True}), 200

@app.route('/api/tariffs/reserve', methods=['POST'])
def reserve_stock():
    """Резервирование тарифов (уменьшение остатков)"""
    data = request.get_json()
    tariff_ids = data.get('tariff_ids', [])
    
    for tid in tariff_ids:
        tariff = Tariff.query.get(tid)
        if tariff and tariff.stock > 0:
            tariff.stock -= 1
    db.session.commit()
    
    # Отправить вебхук в invoice service
    try:
        requests.post("http://invoice-service:5002/api/webhooks/tariff", 
                     json={"event": "tariff_reserved", "tariff_ids": tariff_ids}, timeout=2)
    except:
        pass
    
    return jsonify({"reserved": True, "tariff_ids": tariff_ids}), 200

@app.route('/api/tariffs', methods=['POST'])
def create_tariff():
    data = request.get_json()
    tariff = Tariff(
        name=data['name'],
        price=data['price'],
        stock=data.get('stock', 10)
    )
    db.session.add(tariff)
    db.session.commit()

    try:
        requests.post("http://invoice-service:5002/api/webhooks/tariff", 
                     json={"event": "tariff_created", "tariff_id": tariff.id, "price": tariff.price}, timeout=2)
    except:
        pass

    return jsonify(tariff.to_dict()), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
