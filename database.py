import os
from datetime import datetime, timedelta, timezone

from pymongo import MongoClient

from parser import extraer_remitente

BOGOTA = timezone(timedelta(hours=-5))
_cliente = None


def get_db():
    global _cliente
    if _cliente is None:
        _cliente = DBManager()
    return _cliente


class DBManager:
    def __init__(self):
        uri = os.environ.get("MONGO_URI")
        if not uri:
            raise RuntimeError("Define la variable de entorno MONGO_URI")
        self.client = MongoClient(uri, serverSelectionTimeoutMS=8000)
        self.collection = self.client["nequi_database"]["movimientos"]

    def registrar_movimiento(self, tipo, monto, detalle, banco, remitente):
        ahora = datetime.now(BOGOTA)
        if self._es_duplicado(banco, detalle, ahora):
            return "duplicado"

        self.collection.insert_one(
            {
                "fecha": ahora.strftime("%Y-%m-%d %I:%M %p"),
                "fecha_iso": ahora.isoformat(),
                "fecha_raw": ahora,
                "tipo": tipo,
                "monto": monto,
                "detalle": detalle,
                "banco": banco,
                "remitente": remitente,
            }
        )
        limite = ahora - timedelta(days=90)
        self.collection.delete_many({"fecha_raw": {"$lt": limite}})
        return "ok"

    def obtener_ultimos_movimientos(self, limite=100):
        documentos = self.collection.find().sort("_id", -1).limit(limite)
        return [self._documento_a_movimiento(doc) for doc in documentos]

    def _es_duplicado(self, banco, detalle, ahora):
        ultimo = self.collection.find_one(
            {"detalle": detalle, "banco": banco},
            sort=[("_id", -1)],
        )
        if not ultimo:
            return False
        marca = ultimo.get("fecha_raw")
        if not isinstance(marca, datetime):
            return False
        if marca.tzinfo is None:
            marca = marca.replace(tzinfo=BOGOTA)
        return abs((ahora - marca).total_seconds()) < 120

    def _documento_a_movimiento(self, doc):
        detalle = doc.get("detalle", "")
        banco = doc.get("banco") if doc.get("banco") in ("nequi", "nu") else "nequi"
        fecha = doc.get("fecha", "")
        return {
            "tipo": doc.get("tipo", "Ingreso"),
            "monto": doc.get("monto", 0),
            "fecha": doc.get("fecha_iso") or fecha,
            "fecha_texto": fecha,
            "detalle": detalle,
            "banco": banco,
            "remitente": doc.get("remitente") or extraer_remitente(detalle),
        }
