import re

BANCOS = ("nequi", "nu")

_SALIDA = re.compile(
    r"env[ií]o exitoso|ya est[aá] en el nequi destino|"
    r"\benviaste\b|\bpagaste\b|\btransferiste\b",
    re.IGNORECASE,
)
_INGRESO = re.compile(
    r"te enviaron|te envi[oó]|\brecibiste\b|te lleg[oó]|\babonaron\b",
    re.IGNORECASE,
)
_MONTO_PESOS = re.compile(r"\$\s*(\d[\d.,]*)")
_MONTO_SUELTO = re.compile(
    r"(?:te enviaron|te envi[oó]|recibiste|te lleg[oó]|abonaron)"
    r"\s+\$?\s*(\d[\d.,]*)",
    re.IGNORECASE,
)
_REMITENTES = (
    re.compile(r"^(.+?)\s+te envi[oó]\b", re.IGNORECASE),
    re.compile(
        r"(?:recibiste|te lleg[oó])\s+\$?\s*[\d.,]+\s+de\s+(.+)$",
        re.IGNORECASE,
    ),
)


def interpretar_numero(raw):
    texto = (raw or "").strip().strip(".,")
    if not texto:
        return 0.0

    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            entero, decimal = texto.rsplit(",", 1)
            entero = entero.replace(".", "")
        else:
            entero, decimal = texto.rsplit(".", 1)
            entero = entero.replace(",", "")
        if not decimal:
            return float(entero or 0)
        return float(f"{entero}.{decimal}")

    if "." in texto:
        partes = texto.split(".")
        if len(partes) > 1 and all(len(parte) == 3 for parte in partes[1:]):
            return float("".join(partes))
        if len(partes) == 2 and len(partes[1]) <= 2:
            return float(texto)
        return float(texto.replace(".", ""))

    if "," in texto:
        partes = texto.split(",")
        if len(partes) == 2 and 0 < len(partes[1]) <= 2:
            return float(f"{partes[0]}.{partes[1]}")
        if all(len(parte) == 3 for parte in partes[1:]):
            return float("".join(partes))
        return float(texto.replace(",", ""))

    return float(texto)


def extraer_monto(texto):
    coincidencia = _MONTO_PESOS.search(texto) or _MONTO_SUELTO.search(texto)
    if not coincidencia:
        return 0.0
    try:
        return interpretar_numero(coincidencia.group(1))
    except ValueError:
        return 0.0


def extraer_remitente(texto):
    for patron in _REMITENTES:
        coincidencia = patron.search(texto.strip())
        if not coincidencia:
            continue
        nombre = coincidencia.group(1).strip(" .¡!,")
        if 2 <= len(nombre) <= 60 and not nombre.lower().startswith("te "):
            return nombre
    return ""


def parse_notificacion(texto, banco):
    if not texto or not str(texto).strip() or str(texto).strip() == "{notification}":
        return None

    limpio = str(texto).strip()
    if _SALIDA.search(limpio) or not _INGRESO.search(limpio):
        return None

    monto = extraer_monto(limpio)
    if monto <= 0:
        return None

    banco_final = (banco or "").lower().strip()
    if banco_final not in BANCOS:
        banco_final = "nequi" if "nequi" in limpio.lower() else "nu"

    return {
        "tipo": "Ingreso",
        "monto": monto,
        "detalle": limpio,
        "banco": banco_final,
        "remitente": extraer_remitente(limpio),
    }


def normalizar_movimiento(item):
    if isinstance(item, dict):
        detalle = item.get("detalle") or ""
        banco = (item.get("banco") or "nequi").lower()
        if banco not in BANCOS:
            banco = "nequi"
        try:
            monto = float(item.get("monto") or 0)
        except (TypeError, ValueError):
            monto = 0.0
        return {
            "tipo": item.get("tipo") or "Ingreso",
            "monto": monto,
            "fecha": item.get("fecha_iso") or item.get("fecha") or "",
            "fecha_texto": item.get("fecha_texto") or item.get("fecha") or "",
            "detalle": detalle,
            "banco": banco,
            "remitente": item.get("remitente") or extraer_remitente(detalle),
        }

    if isinstance(item, (list, tuple)) and len(item) >= 4:
        detalle = str(item[3] or "")
        try:
            monto = float(item[1] or 0)
        except (TypeError, ValueError):
            monto = 0.0
        fecha = str(item[2] or "")
        return {
            "tipo": item[0] or "Ingreso",
            "monto": monto,
            "fecha": fecha,
            "fecha_texto": fecha,
            "detalle": detalle,
            "banco": "nequi",
            "remitente": extraer_remitente(detalle),
        }

    return None
