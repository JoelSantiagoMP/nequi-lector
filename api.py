from fastapi import FastAPI, Request
from database import DBManager
import re
import os
import uvicorn

app = FastAPI()
db = DBManager()

@app.post("/nequi-webhook")
async def recibir_notificacion(request: Request):
    data = await request.json()
    texto = data.get("texto_notificacion", "")
    
    match_monto = re.search(r"\$\s?([\d\.]+)", texto)
    monto = float(match_monto.group(1).replace(".", "")) if match_monto else 0.0
    
    texto_min = texto.lower()
    es_ingreso = any(p in texto_min for p in ["recibiste", "enviaron", "pusieron", "transfirio"])
    tipo = "Ingreso" if es_ingreso else "Egreso"

    concepto = "Movimiento Nequi"
    if " de " in texto_min: concepto = texto.split(" de ")[-1]
    elif " a " in texto_min: concepto = texto.split(" a ")[-1]
    elif " en " in texto_min: concepto = texto.split(" en ")[-1]
    
    concepto = concepto[:30].strip()

    if monto > 0:
        db.registrar_movimiento(tipo, monto, concepto) 
        return {"status": "success"}
    return {"status": "ignored"}

@app.get("/datos")
async def obtener_datos_nube():
    try:
        ingresos, egresos = db.obtener_resumen_mensual()
        movimientos = db.obtener_ultimos_movimientos()
        return {
            "ingresos": float(ingresos),
            "gastos": float(egresos),
            "movimientos": movimientos
        }
    except Exception as e:
        print(f"Error en API: {e}")
        return {"ingresos": 0, "gastos": 0, "movimientos": []}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
