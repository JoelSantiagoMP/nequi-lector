import flet as ft
import requests
import threading
import time

URL_API = "https://nequi-lector.onrender.com/movimientos" 

def main(page: ft.Page):
    page.title = "Nequi Tracker Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F5F5F5"
    page.padding = 20

    # Nequi Colors
    PRIMARY_PURPLE = "#700EBE"
    NEON_PINK = "#FF0082"
    WHITE = "#FFFFFF"
    
    lista_movimientos = ft.ListView(spacing=12, expand=True)
    txt_ingresos = ft.Text("Cargando...", size=18, weight="bold", color=WHITE)
    status_text = ft.Text("Conectando al servidor...", size=12, color="grey600", italic=True)

    def create_card(item):
        # item: [tipo, monto, fecha, detalle]
        monto = item[1]
        fecha = item[2]
        detalle = item[3]

        detail_container = ft.Container(
            content=ft.Text(detalle, size=14, color="grey800"),
            visible=False,
            margin=ft.margin.only(top=10)
        )

        def toggle_expand(e):
            detail_container.visible = not detail_container.visible
            e.control.update()

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon("arrow_downward", color=NEON_PINK, size=20),
                        bgcolor="#FCE4EC", padding=10, border_radius=25,
                    ),
                    ft.Column([
                        ft.Text("Ingreso Recibido", weight="bold", size=16, color=PRIMARY_PURPLE),
                        ft.Text(fecha, size=12, color="grey600"),
                    ], expand=True, spacing=2),
                    ft.Text(f"+${monto:,.0f}", size=18, weight="bold", color=PRIMARY_PURPLE)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                detail_container
            ], spacing=0),
            padding=15, 
            border_radius=12, 
            bgcolor=WHITE,
            border=ft.border.all(1, "#E0E0E0"),
            on_click=toggle_expand,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
        )

    def actualizar_lista():
        try:
            # Si no hay controles cargados, indicar al usuario que está conectando
            if not lista_movimientos.controls:
                status_text.value = "Conectando con Render (puede tardar hasta 2 minutos si el servidor está en cold start)..."
                status_text.color = "grey600"
                page.update()

            response = requests.get(URL_API, timeout=120) # Aumentado a 120s
            if response.status_code == 200:
                movimientos = response.json() 
                
                # Fechas para filtrar
                fecha_hoy = time.strftime("%Y-%m-%d")
                mes_actual = time.strftime("%Y-%m")

                ing_hoy = 0
                ing_mes = 0
                
                nuevos_controles = []
                for item in movimientos:
                    # Garantizar que el monto sea float
                    try:
                        monto_item = float(item[1])
                    except (ValueError, TypeError):
                        monto_item = 0.0

                    # Sumar a totales
                    fecha_item = item[2]
                    if isinstance(fecha_item, str):
                        if fecha_item.startswith(fecha_hoy):
                            ing_hoy += monto_item
                        if fecha_item.startswith(mes_actual):
                            ing_mes += monto_item
                    
                    # Añadir a la lista
                    item_procesado = [item[0], monto_item, item[2], item[3]]
                    nuevos_controles.append(create_card(item_procesado))
                
                txt_ingresos.value = f"Hoy: ${ing_hoy:,.0f} | Mes: ${ing_mes:,.0f}"
                lista_movimientos.controls = nuevos_controles
                status_text.value = "Conectado al servidor"
                status_text.color = "green"
                status_text.visible = False # Ocultar si todo está correcto
                page.update()
            else:
                raise Exception(f"Servidor respondió con código {response.status_code}")
        except Exception as e:
            print(f"Error actualizando lista: {e}")
            txt_ingresos.value = "Error de conexión"
            status_text.value = f"Error: {e}\n(Verifica que el servidor esté activo y el celular tenga internet)"
            status_text.color = "red"
            status_text.visible = True
            page.update()

    # UI Assembly
    page.add(
        ft.Column([
            ft.Text("Mi Nequi", size=28, weight="bold", color=PRIMARY_PURPLE),
            ft.Container(
                content=ft.Column([
                    ft.Text("TOTAL INGRESOS", size=12, color="#E0B0FF", weight="bold"), 
                    txt_ingresos
                ]),
                bgcolor=PRIMARY_PURPLE, 
                padding=20, 
                border_radius=12,
                alignment=ft.Alignment.CENTER_LEFT
            ),
            ft.Text("Historial (Últimos 100)", size=16, weight="bold", color=PRIMARY_PURPLE),
            status_text,
            lista_movimientos
        ], expand=True)
    )

    def run_timer():
        while True:
            actualizar_lista()
            time.sleep(10)

    # Iniciamos el hilo sin bloquear el hilo principal (evita pantalla blanca al iniciar en celular)
    thread = threading.Thread(target=run_timer, daemon=True)
    thread.start()

if __name__ == "__main__":
    ft.app(target=main)
