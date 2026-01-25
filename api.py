from flask import Flask, request, jsonify
from database import DBManager
import re

app = Flask(__name__)
db = DBManager()

def extraer_monto(texto):
    # Detecta números con punto (20.000) o sin punto (20000)
    patron = r'\d[\d\.]+' 
    resultados = re.findall(patron, texto)
    
    for res in resultados:
        # Limpieza total: quitamos puntos y espacios
        valor_limpio = res.replace('.', '').strip()
        
        if valor_limpio.isdigit():
            monto = float(valor_limpio)
            # Rango final acordado: de $1.000 hasta $10.000.000
            if 1000 <= monto <= 10000000: 
                return monto
    return 0.0

def identificar_movimiento(texto):
    t = texto.lower()
    # Lista ultra-reforzada con y sin tildes
    ingreso_keywords = ["te envió", "te envio", "recibiste", "recibio", "envió", "envio", "transferencia"]
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
        return jsonify({"status": "error"}), 400

    mensaje = data['texto_notificacion']
    tipo = identificar_movimiento(mensaje)
    monto = extraer_monto(mensaje)
    
    # Guardamos si identificamos el tipo y encontramos un número coherente
    if tipo != "Otro" and monto > 0:
        db.registrar_movimiento(tipo, monto, mensaje)
        return jsonify({"status": "success", "tipo": tipo, "monto": monto}), 200
    
    return jsonify({"status": "ignored", "reason": "No se detectó monto o tipo"}), 200

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

