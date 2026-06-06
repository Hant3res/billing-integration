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

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "currency": self.currency
        }

with app.app_context():
    db.create_all()
    if Tariff.query.count() == 0:
        test_data = [
            Tariff(name="Hosting Basic", price=500, currency="RUB"),
            Tariff(name="Hosting Pro", price=1500, currency="RUB"),
            Tariff(name="Extra Disk 10GB", price=300, currency="RUB"),
            Tariff(name="SSL Certificate", price=1000, currency="RUB"),
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

@app.route('/api/tariffs', methods=['POST'])
def create_tariff():
    data = request.get_json()
    tariff = Tariff(
        name=data['name'],
        price=data['price'],
        currency=data.get('currency', 'RUB')
    )
    db.session.add(tariff)
    db.session.commit()

    # Webhook to invoice service
    try:
        requests.post("http://invoice-service:5002/api/webhooks/tariff", 
                     json={"event": "tariff_created", "tariff_id": tariff.id, "price": tariff.price}, timeout=2)
    except:
        pass

    return jsonify(tariff.to_dict()), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
