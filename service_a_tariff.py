from flask import Flask, jsonify

app = Flask(__name__)

tariffs = [
    {"id": 1, "name": "Хостинг Basic", "price": 500, "currency": "RUB"},
    {"id": 2, "name": "Хостинг Pro", "price": 1500, "currency": "RUB"},
    {"id": 3, "name": "Доп. диск 10GB", "price": 300, "currency": "RUB"},
    {"id": 4, "name": "SSL-сертификат", "price": 1000, "currency": "RUB"},
]

@app.route('/api/tariffs', methods=['GET'])
def get_tariffs():
    return jsonify({"tariffs": tariffs}), 200

@app.route('/api/tariffs/<int:tariff_id>', methods=['GET'])
def get_tariff(tariff_id):
    tariff = next((t for t in tariffs if t["id"] == tariff_id), None)
    if tariff:
        return jsonify(tariff), 200
    return jsonify({"error": "Tariff not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
