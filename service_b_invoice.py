from flask import Flask, request, jsonify

app = Flask(__name__)

invoices = []
next_id = 1

@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    return jsonify({"invoices": invoices}), 200

@app.route('/api/invoices/create', methods=['POST'])
def create_invoice():
    global next_id
    data = request.get_json()
    
    client_id = data.get('client_id')
    tariff_ids = data.get('tariff_ids', [])
    
    if not client_id or not tariff_ids:
        return jsonify({"error": "client_id and tariff_ids required"}), 400
    
    total_amount = len(tariff_ids) * 500
    
    invoice = {
        "id": next_id,
        "client_id": client_id,
        "tariff_ids": tariff_ids,
        "total_amount": total_amount,
        "currency": "RUB",
        "status": "pending",
        "created_at": "2026-06-06T10:00:00Z"
    }
    invoices.append(invoice)
    next_id += 1
    
    return jsonify(invoice), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
