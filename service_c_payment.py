from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import requests
import uuid

app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'mssql+pyodbc://sa:YourStrongPass123@localhost:1433/billing_db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

INVOICE_URL = os.getenv('INVOICE_SERVICE_URL', 'http://invoice-service:5002')

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='card')
    status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "payment_method": self.payment_method,
            "status": self.status,
            "transaction_id": self.transaction_id
        }

with app.app_context():
    db.create_all()
    print("Payments table ready")

@app.route('/api/payments', methods=['GET'])
def get_payments():
    payments = Payment.query.all()
    return jsonify({"payments": [p.to_dict() for p in payments]}), 200

@app.route('/api/payments/pay', methods=['POST'])
def process_payment():
    data = request.get_json()
    invoice_id = data['invoice_id']
    method = data.get('payment_method', 'card')

    # Get invoice from invoice service
    try:
        resp = requests.get(f"{INVOICE_URL}/api/invoices")
        if resp.status_code != 200:
            return jsonify({"error": "Invoice service error"}), 503
        invoices = resp.json().get('invoices', [])
        invoice = next((i for i in invoices if i['id'] == invoice_id), None)
        if not invoice:
            return jsonify({"error": "Invoice not found"}), 404
        if invoice['status'] == 'paid':
            return jsonify({"error": "Already paid"}), 400
    except Exception as e:
        return jsonify({"error": "Cannot connect to invoice service"}), 503

    trans_id = str(uuid.uuid4())
    payment = Payment(
        invoice_id=invoice_id,
        amount=invoice['total_amount'],
        payment_method=method,
        status='completed',
        transaction_id=trans_id
    )
    db.session.add(payment)
    db.session.commit()

    # Mark invoice as paid
    try:
        requests.patch(f"{INVOICE_URL}/api/invoices/{invoice_id}/pay", timeout=2)
    except:
        pass

    return jsonify({
        "status": "completed",
        "transaction_id": trans_id,
        "message": f"Payment for invoice {invoice_id} completed"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
