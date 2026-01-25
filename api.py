from flask import Flask, request, jsonify
from database import DBManager
import re

app = Flask(__name__)
db = DBManager()

def extraer_monto(texto):
    # 1. Quitamos los puntos de miles (ej: 1.000 -> 1000)
    texto_limpio = texto.replace('.', '')
    # 2. Buscamos los números
    numeros = re.findall(r'\d+', texto_limpio)
    
    for n in numeros:
        try:
            monto = float(n)
            # Bajamos el filtro a 100 para que 1000 pase sin problemas
            if 100 <= monto <= 10000000:
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
        
        # Procesamos de verdad el mensaje
        monto = extraer_monto(mensaje)
        tipo = identificar_movimiento(mensaje)
        
        # Ahora sí guardamos con los datos reales
        if monto > 0:
            db.registrar_movimiento(tipo, monto, mensaje)
            return jsonify({"status": "success", "monto": monto}), 200
        else:
            # Si el monto es 0, guardamos como error para saber qué falló
            db.registrar_movimiento("ERROR_MONTO", 0, mensaje)
            return jsonify({"status": "ignored", "reason": "monto 0"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/movimientos', methods=['GET'])
def obtener_movimientos():
    return jsonify(db.obtener_ultimos_movimientos())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)


