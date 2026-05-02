from flask import Flask, request, jsonify
from database import DBManager
import re
import sys

app = Flask(__name__)
db = DBManager()

def extraer_monto(texto):
    try:
        # Busca el símbolo de dólar seguido de espacios opcionales y números (con puntos o comas)
        match = re.search(r'\$\s*([\d\.,]+)', texto)
        if match:
            monto_str = match.group(1)
            # Eliminar '.00' o ',00' al final si existen
            monto_str = re.sub(r'[\.,]00$', '', monto_str)
            # Eliminar todos los puntos y comas (separadores de miles)
            monto_str = re.sub(r'[\.,]', '', monto_str)
            monto = float(monto_str)
            
            # Filtro de seguridad: rechazar si es 0 (o definir tu mínimo)
            if monto > 0:
                return monto
    except Exception as e:
        print(f"ERROR EN LOGICA DE MONTO: {e}", file=sys.stderr)
    return 0.0

def identificar_movimiento(texto):
    t = texto.lower()
    if any(p in t for p in ["envi", "recibi", "transferencia", "abono", "ingreso"]):
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

        # 2. Procesar y filtrar solo ingresos
        tipo = identificar_movimiento(mensaje)
        if tipo != "Ingreso":
            print(f"OMITIDO: Movimiento no es Ingreso. Texto: {mensaje}", file=sys.stderr)
            return jsonify({"status": "ignored", "message": "Solo se procesan ingresos"}), 200

        monto = extraer_monto(mensaje)
        if monto <= 0:
            print(f"ERROR: No se pudo extraer un monto válido. Texto: {mensaje}", file=sys.stderr)
            return jsonify({"status": "error", "message": "Monto invalido"}), 400
        
        # 3. LOGS DE DIAGNÓSTICO (Para ver en Render)
        print(f"--- NUEVO INGRESO ---", file=sys.stderr)
        print(f"MENSAJE RECIBIDO: {mensaje}", file=sys.stderr)
        print(f"MONTO EXTRAIDO: {monto}", file=sys.stderr)

        # 4. Intentar guardar en MongoDB
        try:
            db.registrar_movimiento(tipo, monto, mensaje)
            print("EXITO: Guardado en MongoDB", file=sys.stderr)
            return jsonify({"status": "success", "monto": monto, "database": "ok"}), 200
        except Exception as db_err:
            print(f"ERROR DE DATABASE: {db_err}", file=sys.stderr)
            return jsonify({"status": "error_db", "info": str(db_err)}), 500

    except Exception as e:
        print(f"ERROR GENERAL: {e}", file=sys.stderr)
        return jsonify({"status": "error_general", "info": str(e)}), 500

@app.route('/movimientos', methods=['GET'])
def obtener_movimientos():
    return jsonify(db.obtener_ultimos_movimientos())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
