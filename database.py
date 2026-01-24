from pymongo import MongoClient
from datetime import datetime

class DBManager:
    def __init__(self):
        # REEMPLAZA ESTA URL con la que te dé MongoDB Atlas
        self.client = MongoClient("TU_URL_DE_MONGO")
        self.db = self.client['nequi_database']
        self.collection = self.db['movimientos']

    def registrar_movimiento(self, tipo, monto, detalle):
        fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nuevo_doc = {
            "fecha": fecha_hoy,
            "tipo": tipo,
            "monto": monto,
            "detalle": detalle
        }
        self.collection.insert_one(nuevo_doc)

    def obtener_ultimos_movimientos(self, limite=15):
        # Buscamos y ordenamos por fecha/id de forma descendente
        docs = self.collection.find().sort("_id", -1).limit(limite)
        # Convertimos al formato de lista que espera tu main.py
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
