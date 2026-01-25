from flask import Flask, request, jsonify
from database import DBManager
import re

app = Flask(__name__)
db = DBManager()

def extraer_monto(texto):
    try:
        # 1. Limpieza inicial: quitamos símbolos de moneda y espacios
        t = texto.replace('$', '').replace(' ', '')
        
        # 2. Manejo de decimales de Bre-B/Nu ($1000.00)
        # Si el texto tiene un punto seguido de dos ceros al final, los borramos
        t = re.sub(r'[\.,]00.*$', '', t)
        
        # 3. Quitamos cualquier otro punto o coma de miles
        t = t.replace('.', '').replace(',', '')
        
        # 4. Buscamos el bloque de números más largo
        numeros = re.findall(r'\d+', t)
        if numeros:
            monto_str = max(numeros, key=len)
            monto = float(monto_str)
            # Filtro de seguridad (100 pesos a 10 millones)
            if 100 <= monto <= 10000000:
                return monto
    except Exception as e:
        print(f"Error procesando monto: {e}")
    return 0.0

def identificar_movimiento(texto):
    t = texto.lower()
    # "envi" captura "envió", "enviaste", "enviaron"
    if any(p in t for p in ["enviaste", "pagaste", "compra", "retiro"]):
        return "Gasto"
    if any(p in t for p in ["envi", "recibi", "transferencia", "abono"]):
        return "Ingreso"
    return "Otro"

@app.route('/nequi-webhook', methods=['POST', 'GET'])
def webhook():
    try:
        # Prioridad a los parámetros de consulta (lo que usa MacroDroid ahora)
        mensaje = request.args.get('texto_notificacion')
        
        if not mensaje:
            data = request.get_json(silent=True)
            if data:
                mensaje = data.get('texto_notificacion')

        if not mensaje:
            return jsonify({"status": "error", "message": "No llego texto"}), 400

        monto = extraer_monto(mensaje)
        tipo = identificar_movimiento(mensaje)
        
        # Guardamos TODO para no perder rastro
        if monto > 0:
            db.registrar_movimiento(tipo, monto, mensaje)
            return jsonify({"status": "success", "monto": monto}), 200
        else:
            # Si no detecta monto, guarda como DEBUG para que lo veas en Atlas
            db.registrar_movimiento("DEBUG_LLEGO", 0, mensaje)
            return jsonify({"status": "ok_sin_monto", "texto": mensaje}), 200

    except Exception as e:
        # Esto evitará el error 500 genérico y nos dirá qué falló
        return jsonify({"status": "error", "error_info": str(e)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
