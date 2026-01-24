from flask import Flask, request, jsonify
from database import DBManager
import re

app = Flask(__name__)
db = DBManager()

def extraer_monto(texto):
    # Busca números con puntos de miles como 10.000 o 1.000.000
    patron = r'\$\s?([0-9]{1,3}(?:\.[0-9]{3})*)'
    resultado = re.search(patron, texto)
    if resultado:
        valor_str = resultado.group(1).replace('.', '')
        return float(valor_str)
    return 0.0

def identificar_movimiento(texto):
    # Convertimos todo a minúsculas para que sea más fácil comparar
    t = texto.lower()
    
    # Palabras clave para entradas de dinero
    ingreso_keywords = ["te envió", "recibiste", "hizo un envío", "envió", "recibido", "transferencia"]
    # Palabras clave para salidas de dinero
    egreso_keywords = ["enviaste", "pagaste", "sacaste", "retiro", "pago", "compra"]

    if any(key in t for key in ingreso_keywords):
        return "Ingreso"
    elif any(key in t for key in egreso_keywords):
        return "Egreso"
    return "Otro"

@app.route('/nequi-webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data or 'texto_notificacion' not in data:
        return jsonify({"status": "error", "message": "No data"}), 400

    mensaje = data['texto_notificacion']
    tipo = identificar_movimiento(mensaje)
    monto = extraer_monto(mensaje)
    
    # Solo guardamos si identificamos que es un movimiento real
    if tipo != "Otro" and monto > 0:
        db.registrar_movimiento(tipo, monto, mensaje)
        return jsonify({"status": "success", "tipo": tipo, "monto": monto}), 200
    
    return jsonify({"status": "ignored", "reason": "No es un movimiento financiero claro"}), 200

@app.route('/movimientos', methods=['GET'])
def obtener_movimientos():
    movs = db.obtener_ultimos_movimientos()
    return jsonify(movs)

@app.route('/resumen', methods=['GET'])
def obtener_resumen():
    ingresos, egresos = db.obtener_resumen_mensual()
    return jsonify({"ingresos": ingresos, "egresos": egresos})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
