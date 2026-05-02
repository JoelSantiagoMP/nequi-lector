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
    txt_ingresos = ft.Text("Hoy: $0 | Mes: $0", size=18, weight="bold", color=WHITE)

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
                        content=ft.Icon(ft.icons.ARROW_DOWNWARD, color=NEON_PINK, size=20),
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
            response = requests.get(URL_API, timeout=10)
            if response.status_code == 200:
                movimientos = response.json() 
                
                # Fechas para filtrar
                fecha_hoy = time.strftime("%Y-%m-%d")
                mes_actual = time.strftime("%Y-%m")

                ing_hoy = 0
                ing_mes = 0
                
                nuevos_controles = []
                for item in movimientos:
                    # Sumar a totales
                    fecha_item = item[2]
                    monto_item = item[1]
                    if isinstance(fecha_item, str):
                        if fecha_item.startswith(fecha_hoy):
                            ing_hoy += monto_item
                        if fecha_item.startswith(mes_actual):
                            ing_mes += monto_item
                    
                    # Añadir a la lista
                    nuevos_controles.append(create_card(item))
                
                txt_ingresos.value = f"Hoy: ${ing_hoy:,.0f} | Mes: ${ing_mes:,.0f}"
                lista_movimientos.controls = nuevos_controles
                page.update()
        except Exception as e:
            print(f"Error actualizando lista: {e}")

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
                alignment=ft.alignment.center_left
            ),
            ft.Text("Historial (Últimos 100)", size=16, weight="bold", color=PRIMARY_PURPLE),
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
