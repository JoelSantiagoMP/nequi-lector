import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from database import get_db
from parser import parse_notificacion

app = Flask(__name__)
CORS(app)


def _autorizado():
    esperado = os.environ.get("WEBHOOK_TOKEN")
    if not esperado:
        return True
    recibido = request.args.get("token") or request.headers.get("X-Webhook-Token")
    return recibido == esperado


def _mensaje():
    texto = request.args.get("texto_notificacion")
    if texto:
        return texto
    data = request.get_json(silent=True) or {}
    return data.get("texto_notificacion")


def procesar(banco):
    if not _autorizado():
        return jsonify({"status": "error", "message": "No autorizado"}), 401

    mensaje = _mensaje()
    if not mensaje:
        return jsonify({"status": "error", "message": "No llego texto"}), 400

    resultado = parse_notificacion(mensaje, banco)
    if resultado is None:
        return jsonify({"status": "ignored", "message": "Solo se procesan ingresos"}), 200

    try:
        estado = get_db().registrar_movimiento(
            resultado["tipo"],
            resultado["monto"],
            resultado["detalle"],
            resultado["banco"],
            resultado["remitente"],
        )
    except Exception as error:
        return jsonify({"status": "error_db", "info": str(error)}), 500

    if estado == "duplicado":
        return jsonify({"status": "duplicate", "monto": resultado["monto"]}), 200
    return jsonify(
        {
            "status": "success",
            "monto": resultado["monto"],
            "banco": resultado["banco"],
            "database": "ok",
        }
    ), 200


@app.route("/webhook/nequi", methods=["POST", "GET"])
@app.route("/nequi-webhook", methods=["POST", "GET"])
def webhook_nequi():
    return procesar("nequi")


@app.route("/webhook/nu", methods=["POST", "GET"])
def webhook_nu():
    return procesar("nu")


@app.route("/movimientos", methods=["GET"])
def obtener_movimientos():
    try:
        movimientos = get_db().obtener_ultimos_movimientos()
    except Exception as error:
        return jsonify({"status": "error_db", "info": str(error)}), 500

    if request.args.get("formato") == "objeto":
        return jsonify(movimientos)
    return jsonify(
        [
            [item["tipo"], item["monto"], item["fecha_texto"] or item["fecha"], item["detalle"]]
            for item in movimientos
        ]
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
