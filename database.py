from pymongo import MongoClient
from datetime import datetime, timedelta

class DBManager:
    def __init__(self):
        # Tu URL real de MongoDB Atlas
        self.uri = "mongodb+srv://yessirrr1105_db_user:NLwtXyEDfALAiluo@cluster0.bykatji.mongodb.net/?appName=Cluster0"
        self.client = MongoClient(self.uri)
        self.db = self.client['nequi_database']
        self.collection = self.db['movimientos']

    def registrar_movimiento(self, tipo, monto, detalle):
        # Restamos 5 horas a la hora del servidor para que sea hora colombiana
        fecha_colombia = datetime.now() - timedelta(hours=5)
        fecha_str = fecha_colombia.strftime("%Y-%m-%d %I:%M %p") # Formato 12h (AM/PM)
        
        nuevo_doc = {
            "fecha": fecha_str,
            "tipo": tipo,
            "monto": monto,
            "detalle": detalle
        }
        self.collection.insert_one(nuevo_doc)

    def obtener_ultimos_movimientos(self, limite=15):
        docs = self.collection.find().sort("_id", -1).limit(limite)
        return [[d['tipo'], d['monto'], d['fecha'], d['detalle']] for d in docs]

    def obtener_resumen_mensual(self):
        mes_actual = datetime.now().strftime("%Y-%m")
        movimientos = self.collection.find({"fecha": {"$regex": f"^{mes_actual}"}})
        ingresos = 0.0
        egresos = 0.0
        for doc in movimientos:
            if doc['tipo'] == 'Ingreso':
                ingresos += doc['monto']
            else:
                egresos += doc['monto']
        return ingresos, egresos

