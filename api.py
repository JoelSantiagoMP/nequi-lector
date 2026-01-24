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
    
    # 1. Extraer Monto
    match_monto = re.search(r"\$\s?([\d\.]+)", texto)
    monto = float(match_monto.group(1).replace(".", "")) if match_monto else 0.0
    
    # 2. Clasificar tipo
    texto_min = texto.lower()
    es_ingreso = any(p in texto_min for p in ["recibiste", "enviaron", "pusieron", "transfirio"])
    tipo = "Ingreso" if es_ingreso else "Egreso"

    # 3. Extraer concepto (Quién envía o dónde se gasta)
    concepto = "Movimiento Nequi"
    if " de " in texto_min:
        concepto = texto.split(" de ")[-1]
    elif " a " in texto_min:
        concepto = texto.split(" a ")[-1]
    elif " en " in texto_min:
        concepto = texto.split(" en ")[-1]
    
    concepto = concepto[:30].strip()

    if monto > 0:
        db.registrar_movimiento(tipo, monto, concepto) 
        print(f"✅ Guardado: {tipo} ${monto} - {concepto}")
        return {"status": "success"}
    
    return {"status": "ignored"}

# ESTA ES LA FUNCIÓN PARA QUE TU PC Y TABLET VEAN LOS DATOS
@app.get("/datos")
async def obtener_datos_nube():
    try:
        ingresos, gastos = db.obtener_resumen_mensual()
        movimientos = db.obtener_ultimos_movimientos()
        return {
            "ingresos": float(ingresos or 0),
            "gastos": float(gastos or 0),
            "movimientos": movimientos or []
        }
    except Exception as e:
        return {"ingresos": 0, "gastos": 0, "movimientos": []}


@app.get("/")
def home():
    return {"mensaje": "Servidor Nequi Cloud Activo"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


