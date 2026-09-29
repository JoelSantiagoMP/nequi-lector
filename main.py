import asyncio
import re
from datetime import datetime, timedelta, timezone

import flet as ft
import requests

from parser import normalizar_movimiento

URL_API = "https://nequi-lector.onrender.com/movimientos?formato=objeto"
BOGOTA = timezone(timedelta(hours=-5))
MESES = (
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
)

MARCAS = {
    "nequi": {
        "nombre": "Nequi",
        "letra": "N",
        "fondo": "#200020",
        "texto": "#FFFFFF",
        "secundario": "#E7B6D4",
        "acento": "#DA0081",
        "borde": "#200020",
    },
    "nu": {
        "nombre": "Nu",
        "letra": "Nu",
        "fondo": "#FFFFFF",
        "texto": "#191919",
        "secundario": "#6B6570",
        "acento": "#820AD1",
        "borde": "#E4D4F4",
    },
}


def dinero(valor):
    return "$" + f"{valor:,.0f}".replace(",", ".")


def parse_fecha(valor):
    if not valor:
        return None
    texto = str(valor).strip()
    try:
        marca = datetime.fromisoformat(texto)
        if marca.tzinfo is None:
            marca = marca.replace(tzinfo=BOGOTA)
        return marca.astimezone(BOGOTA)
    except ValueError:
        pass

    coincidencia = re.match(
        r"(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})\s*([AaPp])",
        texto,
    )
    if not coincidencia:
        return None
    anio, mes, dia, hora, minuto, turno = coincidencia.groups()
    hora = int(hora) % 12
    if turno.lower() == "p":
        hora += 12
    return datetime(
        int(anio), int(mes), int(dia), hora, int(minuto), tzinfo=BOGOTA
    )


def etiqueta_fecha(valor, respaldo=""):
    marca = parse_fecha(valor) or parse_fecha(respaldo)
    if marca is None:
        return respaldo or str(valor or "")
    hora = marca.hour % 12 or 12
    sufijo = "a. m." if marca.hour < 12 else "p. m."
    reloj = f"{hora}:{marca.minute:02d} {sufijo}"
    hoy = datetime.now(BOGOTA).date()
    if marca.date() == hoy:
        return f"Hoy · {reloj}"
    if marca.date() == hoy - timedelta(days=1):
        return f"Ayer · {reloj}"
    return f"{marca.day} {MESES[marca.month - 1]} · {reloj}"


def descargar():
    respuesta = requests.get(URL_API, timeout=120)
    respuesta.raise_for_status()
    datos = respuesta.json()
    if not isinstance(datos, list):
        raise ValueError("La respuesta no es una lista")
    movimientos = []
    for item in datos:
        normalizado = normalizar_movimiento(item)
        if normalizado and normalizado["tipo"] == "Ingreso" and normalizado["monto"] > 0:
            movimientos.append(normalizado)
    return movimientos


def main(page: ft.Page):
    page.title = "Movimientos"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F4F0F6"
    page.padding = ft.Padding.all(16)
    page.scroll = ft.ScrollMode.AUTO

    estado = {"movimientos": [], "filtro": "todos", "error": None}
    totales = {
        banco: {"hoy": ft.Text("—", size=22, weight=ft.FontWeight.BOLD), "mes": ft.Text("Mes —", size=13)}
        for banco in ("nequi", "nu")
    }
    for banco, marca in MARCAS.items():
        totales[banco]["hoy"].color = marca["texto"]
        totales[banco]["mes"].color = marca["secundario"]

    historial = ft.Column(spacing=10)
    aviso = ft.Text("Conectando", size=12, color="#FFFFFF")
    pastilla = ft.Container(
        content=aviso,
        bgcolor="#7A7480",
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border_radius=ft.BorderRadius.all(20),
    )
    filtros = {}

    def tarjeta_marca(banco):
        marca = MARCAS[banco]
        return ft.Container(
            expand=True,
            bgcolor=marca["fondo"],
            border=ft.Border.all(1, marca["borde"]),
            border_radius=ft.BorderRadius.all(22),
            padding=ft.Padding.all(16),
            content=ft.Column(
                [
                    ft.Text(marca["nombre"].upper(), size=11, weight=ft.FontWeight.BOLD, color=marca["acento"]),
                    totales[banco]["hoy"],
                    totales[banco]["mes"],
                ],
                spacing=4,
            ),
        )

    def estilo_filtro(clave, activo):
        colores = {
            "todos": ("#191919", "#FFFFFF"),
            "nequi": ("#DA0081", "#FFFFFF"),
            "nu": ("#820AD1", "#FFFFFF"),
        }
        fondo, texto = colores[clave] if activo else ("#FFFFFF", "#3A3340")
        boton = filtros[clave]
        boton.bgcolor = fondo
        boton.border = ft.Border.all(1, fondo if activo else "#E4E0E8")
        boton.content.color = texto

    def crear_tarjeta(item):
        marca = MARCAS.get(item["banco"], MARCAS["nequi"])
        detalle = ft.Container(
            visible=False,
            padding=ft.Padding.only(top=10),
            content=ft.Text(item["detalle"], size=13, color="#5C5563"),
        )

        def alternar(_evento):
            detalle.visible = not detalle.visible
            detalle.update()

        quien = item["remitente"] or "Transferencia"
        cuando = etiqueta_fecha(item["fecha"], item.get("fecha_texto", ""))
        return ft.Container(
            bgcolor="#FFFFFF",
            border_radius=ft.BorderRadius.all(18),
            padding=ft.Padding.all(14),
            on_click=alternar,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                width=42,
                                height=42,
                                bgcolor=marca["acento"],
                                border_radius=ft.BorderRadius.all(21),
                                alignment=ft.Alignment.CENTER,
                                content=ft.Text(
                                    marca["letra"],
                                    color="#FFFFFF",
                                    weight=ft.FontWeight.BOLD,
                                    size=14 if item["banco"] == "nu" else 16,
                                ),
                            ),
                            ft.Column(
                                [
                                    ft.Text(quien, size=15, weight=ft.FontWeight.BOLD, color="#191919"),
                                    ft.Text(
                                        f"{marca['nombre']} · {cuando}",
                                        size=12,
                                        color="#6B6570",
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Text(
                                dinero(item["monto"]),
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=marca["acento"],
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    detalle,
                ],
                spacing=0,
            ),
        )

    def pintar():
        ahora = datetime.now(BOGOTA)
        hoy = ahora.date()
        mes = ahora.strftime("%Y-%m")
        sumas = {banco: {"hoy": 0.0, "mes": 0.0} for banco in MARCAS}
        for item in estado["movimientos"]:
            marca_tiempo = parse_fecha(item["fecha"]) or parse_fecha(item.get("fecha_texto", ""))
            if marca_tiempo is None or item["banco"] not in sumas:
                continue
            if marca_tiempo.date() == hoy:
                sumas[item["banco"]]["hoy"] += item["monto"]
            if marca_tiempo.strftime("%Y-%m") == mes:
                sumas[item["banco"]]["mes"] += item["monto"]

        for banco in MARCAS:
            totales[banco]["hoy"].value = dinero(sumas[banco]["hoy"])
            totales[banco]["mes"].value = f"Este mes {dinero(sumas[banco]['mes'])}"

        visibles = [
            item
            for item in estado["movimientos"]
            if estado["filtro"] == "todos" or item["banco"] == estado["filtro"]
        ]
        if estado["error"] and not visibles:
            aviso.value = "Sin conexión"
            pastilla.bgcolor = "#C62828"
            historial.controls = [
                ft.Text(estado["error"], size=13, color="#8A3040")
            ]
        else:
            if estado["error"]:
                aviso.value = "Sin conexión"
                pastilla.bgcolor = "#C62828"
            else:
                aviso.value = "En línea"
                pastilla.bgcolor = "#2E7D32"
            if visibles:
                historial.controls = [crear_tarjeta(item) for item in visibles]
            else:
                historial.controls = [
                    ft.Container(
                        padding=ft.Padding.symmetric(vertical=28),
                        content=ft.Text(
                            "Sin ingresos por aquí",
                            size=15,
                            color="#6B6570",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    )
                ]
        for clave in filtros:
            estilo_filtro(clave, clave == estado["filtro"])
        page.update()

    def elegir(clave):
        def accion(_evento):
            estado["filtro"] = clave
            pintar()

        return accion

    def chip(clave, etiqueta):
        control = ft.Container(
            border_radius=ft.BorderRadius.all(20),
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            on_click=elegir(clave),
            content=ft.Text(etiqueta, size=13, weight=ft.FontWeight.BOLD),
        )
        filtros[clave] = control
        return control

    async def vigilar():
        while True:
            try:
                estado["movimientos"] = await asyncio.to_thread(descargar)
                estado["error"] = None
            except Exception as error:
                estado["error"] = (
                    "El servidor puede tardar un minuto en despertar. "
                    f"{error}"
                )
            pintar()
            await asyncio.sleep(10)

    page.add(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Movimientos", size=30, weight=ft.FontWeight.BOLD, color="#191919"),
                                ft.Text("Nequi y Nu", size=14, color="#6B6570"),
                            ],
                            spacing=0,
                            expand=True,
                        ),
                        pastilla,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=14),
                ft.Row([tarjeta_marca("nequi"), tarjeta_marca("nu")], spacing=10),
                ft.Container(height=14),
                ft.Row(
                    [chip("todos", "Todos"), chip("nequi", "Nequi"), chip("nu", "Nu")],
                    spacing=8,
                ),
                ft.Container(height=8),
                historial,
            ],
            spacing=0,
        )
    )
    estilo_filtro("todos", True)
    estilo_filtro("nequi", False)
    estilo_filtro("nu", False)
    page.update()
    page.run_task(vigilar)


if __name__ == "__main__":
    ft.run(main)
