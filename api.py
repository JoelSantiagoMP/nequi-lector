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
    try:
        data = request.get_json(force=True)
        mensaje = data.get('texto_notificacion', 'VACIO')
        
        # GUARDADO FORZADO: No preguntamos nada, solo guardamos para probar
        db.registrar_movimiento("PRUEBA_NOTIF", 0, mensaje)
        
        return jsonify({"status": "success", "recibido": mensaje}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/movimientos', methods=['GET'])
def obtener_movimientos():
    return jsonify(db.obtener_ultimos_movimientos())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

