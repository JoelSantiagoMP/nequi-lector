from flask import Flask, request, jsonify
from database import DBManager
import re
import sys

app = Flask(__name__)
db = DBManager()

def extraer_monto(texto):
    try:
        # 1. Limpieza radical: quitamos signo $, espacios y puntos de miles
        t = texto.replace('$', '').replace(' ', '')
        
        # 2. Manejo de centavos (.00) - los eliminamos para no confundirlos con miles
        # Busca un punto o coma seguido de dos ceros al final del número
        t = re.sub(r'[\.,]00.*$', '', t)
        
        # 3. Quitamos puntos restantes (ej: 1.000 -> 1000)
        t = t.replace('.', '').replace(',', '')
        
        # 4. Buscamos números
        numeros = re.findall(r'\d+', t)
        if numeros:
            # Tomamos el número más largo encontrado
            monto_str = max(numeros, key=len)
            monto = float(monto_str)
            
            # Filtro de seguridad
            if 100 <= monto <= 10000000:
                return monto
    except Exception as e:
        print(f"ERROR EN LOGICA DE MONTO: {e}", file=sys.stderr)
    return 0.0

def identificar_movimiento(texto):
    t = texto.lower()
    if any(p in t for p in ["enviaste", "pagaste", "compra", "retiro"]):
        return "Gasto"
    if any(p in t for p in ["envi", "recibi", "transferencia", "abono"]):
        return "Ingreso"
    return "Otro"

@app.route('/nequi-webhook', methods=['POST', 'GET'])
def webhook():
    try:
        # 1. Capturar el mensaje (Parámetro o JSON)
        mensaje = request.args.get('texto_notificacion')
        if not mensaje:
            data = request.get_json(silent=True)
            if data:
                mensaje = data.get('texto_notificacion')

        if not mensaje:
            print("ERROR: No se recibió ningún texto en la petición", file=sys.stderr)
            return jsonify({"status": "error", "message": "No llego texto"}), 400

        # 2. Procesar
        monto = extraer_monto(mensaje)
        tipo = identificar_movimiento(mensaje)
        
        # 3. LOGS DE DIAGNÓSTICO (Para ver en Render)
        print(f"--- NUEVA TRANSACCION ---", file=sys.stderr)
        print(f"MENSAJE RECIBIDO: {mensaje}", file=sys.stderr)
        print(f"MONTO EXTRAIDO: {monto}", file=sys.stderr)
        print(f"TIPO: {tipo}", file=sys.stderr)

        # 4. Intentar guardar en MongoDB
        try:
            db.registrar_movimiento(tipo, monto, mensaje)
            print("EXITO: Guardado en MongoDB", file=sys.stderr)
            return jsonify({"status": "success", "monto": monto, "database": "ok"}), 200
        except Exception as db_err:
            print(f"ERROR DE DATABASE: {db_err}", file=sys.stderr)
            return jsonify({"status": "error_db", "info": str(db_err)}), 200

    except Exception as e:
        print(f"ERROR GENERAL: {e}", file=sys.stderr)
        return jsonify({"status": "error_general", "info": str(e)}), 200

@app.route('/movimientos', methods=['GET'])
def obtener_movimientos():
    return jsonify(db.obtener_ultimos_movimientos())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
