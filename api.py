from flask import Flask, request, jsonify
from database import DBManager
import re

app = Flask(__name__)
db = DBManager()

def extraer_monto(texto):
    # Buscamos secuencias de números (ej: 1.000 o 1000)
    numeros = re.findall(r'\d+(?:\.\d+)?', texto.replace(',', ''))
    for n in numeros:
        try:
            monto = float(n)
            # Filtro para evitar números pequeños que no son montos (como fechas o códigos)
            if 1000 <= monto <= 10000000:
                return monto
        except:
            continue
    return 0.0

def identificar_movimiento(texto):
    t = texto.lower()
    # Palabras clave sin tildes para evitar errores de codificación
    if any(palabra in t for palabra in ["enviaste", "pagaste", "compra", "retiro"]):
        return "Gasto"
    if any(palabra in t for palabra in ["envi", "recibi", "transferencia", "abono"]):
        return "Ingreso"
    return "Otro"

@app.route('/nequi-webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data or 'texto_notificacion' not in data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    mensaje = data['texto_notificacion']
    tipo = identificar_movimiento(mensaje)
    monto = extraer_monto(mensaje)
    
    # SOLO GUARDAR SI ES DINERO REAL
    if tipo != "Otro" and monto > 0:
        db.registrar_movimiento(tipo, monto, mensaje)
        return jsonify({"status": "success", "saved": True}), 200
    
    # Si es publicidad o un mensaje sin monto, no lo guardamos pero respondemos OK
    return jsonify({"status": "ignored", "reason": "No financial data detected"}), 200

@app.route('/movimientos', methods=['GET'])
def obtener_movimientos():
    return jsonify(db.obtener_ultimos_movimientos())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
