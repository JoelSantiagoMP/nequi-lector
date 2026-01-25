from flask import Flask, request, jsonify
from database import DBManager
import re

app = Flask(__name__)
db = DBManager()

def extraer_monto(texto):
    # Busca números que puedan tener puntos o comas
    resultados = re.findall(r'[\d\.,]+', texto)
    for res in resultados:
        limpio = res.replace('.', '').replace(',', '').strip()
        if limpio.isdigit():
            monto = float(limpio)
            if 1000 <= monto <= 10000000:
                return monto
    return 0.0

def identificar_movimiento(texto):
    t = texto.lower()
    # Palabras clave simplificadas para evitar errores de tildes
    if "enviaste" in t or "pagaste" in t or "retiro" in t or "compra" in t:
        return "Gasto"
    if "envi" in t or "recibi" in t or "transferencia" in t:
        return "Ingreso"
    return "Otro"

@app.route('/nequi-webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data or 'texto_notificacion' not in data:
        return jsonify({"status": "error"}), 400

    mensaje = data['texto_notificacion']
    tipo = identificar_movimiento(mensaje)
    monto = extraer_monto(mensaje)
    
    if tipo != "Otro" and monto > 0:
        db.registrar_movimiento(tipo, monto, mensaje)
        return jsonify({"status": "success", "tipo": tipo, "monto": monto}), 200
    
    return jsonify({"status": "ignored", "reason": "No detectado"}), 200

@app.route('/movimientos', methods=['GET'])
def obtener_movimientos():
    return jsonify(db.obtener_ultimos_movimientos())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
