from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import json
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'mssql+pyodbc://sa:YourStrongPass123@localhost:1433/billing_db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.Integer, nullable=False)
    tariff_ids = db.Column(db.String(500), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='RUB')
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.String(50), default=lambda: datetime.now().isoformat())

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "tariff_ids": json.loads(self.tariff_ids) if self.tariff_ids else [],
            "total_amount": self.total_amount,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at
        }

tariff_cache = {}

with app.app_context():
    db.create_all()
    print("Invoices table ready")

@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    invoices = Invoice.query.all()
    return jsonify({"invoices": [inv.to_dict() for inv in invoices]}), 200

@app.route('/api/invoices/create', methods=['POST'])
def create_invoice():
    data = request.get_json()
    client_id = data.get('client_id')
    tariff_ids = data.get('tariff_ids', [])

    if not client_id or not tariff_ids:
        return jsonify({"error": "client_id and tariff_ids required"}), 400

    total = 0
    for tid in tariff_ids:
        total += tariff_cache.get(tid, 500)

    invoice = Invoice(
        client_id=client_id,
        tariff_ids=json.dumps(tariff_ids),
        total_amount=total,
        status='pending'
    )
    db.session.add(invoice)
    db.session.commit()

    return jsonify(invoice.to_dict()), 201

@app.route('/api/invoices/<int:invoice_id>/pay', methods=['PATCH'])
def mark_paid(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({"error": "Not found"}), 404
    invoice.status = 'paid'
    db.session.commit()
    return jsonify(invoice.to_dict()), 200

@app.route('/api/invoices/<int:invoice_id>/cancel', methods=['PATCH'])
def cancel_invoice(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({"error": "Not found"}), 404
    if invoice.status == 'paid':
        return jsonify({"error": "Cannot cancel paid invoice"}), 400
    invoice.status = 'cancelled'
    db.session.commit()
    return jsonify(invoice.to_dict()), 200

@app.route('/api/webhooks/tariff', methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get('event') == 'tariff_created':
        tariff_cache[data['tariff_id']] = data['price']
        print(f"Cached tariff {data['tariff_id']} = {data['price']}")
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
