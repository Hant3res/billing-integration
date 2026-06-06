from flask import Flask, request, jsonify
import requests
import uuid

app = Flask(__name__)

INVOICE_SERVICE_URL = "http://localhost:5002"
payments = []

@app.route('/api/payments', methods=['GET'])
def get_payments():
    return jsonify({"payments": payments}), 200

@app.route('/api/payments/pay', methods=['POST'])
def process_payment():
    data = request.get_json()
    invoice_id = data.get('invoice_id')
    payment_method = data.get('payment_method', 'card')
    
    try:
        resp = requests.get(f"{INVOICE_SERVICE_URL}/api/invoices")
        if resp.status_code != 200:
            return jsonify({"error": "Invoice service unavailable"}), 503
        
        all_invoices = resp.json().get('invoices', [])
        invoice = next((inv for inv in all_invoices if inv['id'] == invoice_id), None)
        
        if not invoice:
            return jsonify({"error": "Invoice not found"}), 404
        
        if invoice['status'] == 'paid':
            return jsonify({"error": "Invoice already paid"}), 400
            
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot connect to Invoice Service"}), 503
    
    payment_status = "completed"
    transaction_id = str(uuid.uuid4())
    
    payment = {
        "id": len(payments) + 1,
        "invoice_id": invoice_id,
        "amount": invoice['total_amount'],
        "payment_method": payment_method,
        "status": payment_status,
        "transaction_id": transaction_id
    }
    payments.append(payment)
    
    return jsonify({
        "status": payment_status,
        "transaction_id": transaction_id,
        "message": f"Payment for invoice {invoice_id} completed"
    }), 200

@app.route('/api/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    payment = next((p for p in payments if p['id'] == payment_id), None)
    if payment:
        return jsonify(payment), 200
    return jsonify({"error": "Payment not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
