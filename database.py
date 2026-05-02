from pymongo import MongoClient
from datetime import datetime, timedelta

class DBManager:
    def __init__(self):
        # Tu URL de MongoDB Atlas con acceso permanente
        self.uri = "mongodb+srv://yessirrr1105_db_user:NLwtXyEDfALAiluo@cluster0.bykatji.mongodb.net/nequi_database?retryWrites=true&w=majority&appName=Cluster0"
        self.client = MongoClient(self.uri)
        self.db = self.client['nequi_database']
        self.collection = self.db['movimientos']

    def registrar_movimiento(self, tipo, monto, detalle):
        # Hora colombiana
        fecha_colombia = datetime.now() - timedelta(hours=5)
        fecha_str = fecha_colombia.strftime("%Y-%m-%d %I:%M %p")
        
        nuevo_doc = {
            "fecha": fecha_str,
            "fecha_raw": fecha_colombia, # Para facilitar el borrado por tiempo
            "tipo": tipo,
            "monto": monto,
            "detalle": detalle
        }
        self.collection.insert_one(nuevo_doc)
        
        # --- AUTO-LIMPIEZA: Borra registros de más de 90 días ---
        limite_tiempo = datetime.now() - timedelta(days=90)
        self.collection.delete_many({"fecha_raw": {"$lt": limite_tiempo}})

    def obtener_ultimos_movimientos(self, limite=100):
        # Aseguramos enviar hasta 100 registros ordenados descendentemente
        docs = self.collection.find().sort("_id", -1).limit(limite)
        return [[d.get('tipo', 'Ingreso'), d.get('monto', 0), d.get('fecha', ''), d.get('detalle', '')] for d in docs]
