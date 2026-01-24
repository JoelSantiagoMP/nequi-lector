import sqlite3
from datetime import datetime

class DBManager:
    def __init__(self, db_name="nequi_pro.db"):
        self.db_name = db_name
        self._crear_tabla()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def _crear_tabla(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimientos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    monto REAL NOT NULL,
                    detalle TEXT
                )
            """)
            conn.commit()

    def registrar_movimiento(self, tipo, monto, detalle):
        fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO movimientos (fecha, tipo, monto, detalle) VALUES (?, ?, ?, ?)",
                (fecha_hoy, tipo, monto, detalle)
            )
            conn.commit()

    def obtener_ultimos_movimientos(self, limite=15):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Obtenemos los 4 datos necesarios para el main.py
            cursor.execute("SELECT tipo, monto, fecha, detalle FROM movimientos ORDER BY id DESC LIMIT ?", (limite,))
            return cursor.fetchall()

    # --- ESTA ES LA FUNCIÓN QUE FALTABA ---
    def obtener_resumen_mensual(self):
        mes_actual = datetime.now().strftime("%Y-%m")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Sumar Ingresos del mes
            cursor.execute("""
                SELECT SUM(monto) FROM movimientos 
                WHERE tipo = 'Ingreso' AND fecha LIKE ?
            """, (f"{mes_actual}%",))
            ingresos = cursor.fetchone()[0] or 0.0

            # Sumar Egresos (Gastos) del mes
            cursor.execute("""
                SELECT SUM(monto) FROM movimientos 
                WHERE tipo = 'Egreso' AND fecha LIKE ?
            """, (f"{mes_actual}%",))
            egresos = cursor.fetchone()[0] or 0.0

            return ingresos, egresos