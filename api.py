from flask import Flask, request, jsonify
from database import DBManager
import re

app = Flask(__name__)
db = DBManager()

def extraer_monto(texto):
    # 1. Limpiamos el texto de puntos y comas para manejar formatos como 1.000 o 1,000
    texto_limpio = texto.replace('.', '').replace(',', '')
    # 2. Buscamos secuencias de números
    numeros = re.findall(r'\d+', texto_limpio)
    
    if numeros:
        # Tomamos el número más largo, que suele ser el monto
        monto_str = max(numeros, key=len)
        try:
            monto = float(monto_str)
            # Filtro: desde 100 pesos hasta 10 millones
            if 100 <= monto <= 10000000:
                return monto
        except:
            pass
    return 0.0

def identificar_movimiento(texto):
    t = texto.lower()
    # Buscamos palabras clave ignorando tildes para evitar errores de codificación
    if any(palabra in t for palabra in ["enviaste", "pagaste", "compra", "retiro"]):
        return "Gasto"
    if any(palabra in t for palabra in ["envi", "recibi", "transferencia", "abono"]):
        return "Ingreso"
    return "Otro"

@app.route('/nequi-webhook', methods=['POST', 'GET'])
def webhook():
    try:
        # INTENTO A: Leer desde Parámetros de Consulta (Configuración actual en 19759.jpg)
        mensaje = request.args.get('texto_notificacion')
        
        # INTENTO B: Si no está en parámetros, buscar en el cuerpo JSON (Por respaldo)
        if not mensaje:
            data = request.get_json(silent=True)
            if data:
                mensaje = data.get('texto_notificacion')

        # Si después de ambos intentos no hay mensaje, devolvemos error
        if not mensaje:
            return jsonify({"status": "error", "message": "No se recibio el texto de la notificacion"}), 400

        # Procesar los datos
        monto = extraer_monto(mensaje)
        tipo = identificar_movimiento(mensaje)
        
        # Guardar en MongoDB
        # Incluso si el monto es 0, lo guardamos como DEBUG para ver qué llegó exactamente
        if monto > 0:
            db.registrar_movimiento(tipo, monto, mensaje)
            return jsonify({"status": "success", "monto": monto, "tipo": tipo}), 200
        else:
            db.registrar_movimiento("DEBUG_LLEGO", 0, mensaje)
            return jsonify({"status": "ok_sin_monto", "mensaje_recibido": mensaje}), 200

    except Exception as e:
        print(f"Error en el servidor: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/movimientos', methods=['GET'])
def obtener_movimientos():
    return jsonify(db.obtener_ultimos_movimientos())

if __name__ == '__main__':
    # Render usa el puerto 10000 por defecto
    app.run(host='0.0.0.0', port=10000)
