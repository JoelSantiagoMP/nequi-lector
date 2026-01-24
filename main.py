import flet as ft
import requests
import threading
import time

# URL CORREGIDA: Apunta a la ruta de movimientos que confirmamos en el navegador
URL_API = "https://nequi-lector.onrender.com/movimientos" 

def main(page: ft.Page):
    page.title = "Nequi Tracker Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    
    lista_movimientos = ft.Column(spacing=10, scroll=ft.ScrollMode.ALWAYS, expand=True)
    txt_ingresos = ft.Text("$0", size=24, weight="bold", color="green400")
    txt_gastos = ft.Text("$0", size=24, weight="bold", color="red400")

    def actualizar_lista():
        try:
            # Consultamos los datos a la nube
            response = requests.get(URL_API, timeout=10)
            if response.status_code == 200:
                # El servidor manda una lista de listas [[tipo, monto, fecha, desc], ...]
                movimientos = response.json() 
                
                # Calculamos totales manualmente ya que el servidor solo manda la lista
                total_ing = sum(item[1] for item in movimientos if item[0] == "Ingreso")
                total_gas = sum(item[1] for item in movimientos if item[0] == "Gasto")
                
                txt_ingresos.value = f"+ ${total_ing:,.0f}"
                txt_gastos.value = f"- ${total_gas:,.0f}"

                lista_movimientos.controls.clear()
                for item in movimientos:
                    es_ing = item[0] == "Ingreso"
                    color = "green400" if es_ing else "red400"
                    simbolo = "+" if es_ing else "-"
                    
                    lista_movimientos.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Text(simbolo, color="white", weight="bold"),
                                    bgcolor=color, padding=10, border_radius=25,
                                ),
                                ft.Column([
                                    ft.Text(str(item[3]).title(), weight="bold", size=16),
                                    ft.Text(item[2], size=11, color="grey500"),
                                ], expand=True),
                                ft.Text(f"{simbolo}${item[1]:,.0f}", 
                                        size=16, weight="bold", color=color)
                            ]),
                            padding=12, border_radius=12, bgcolor="white10"
                        )
                    )
                page.update()
        except Exception as e:
            print(f"Error actualizando datos: {e}")

    page.add(
        ft.Column([
            ft.Text("Mi Nequi Tracker", size=28, weight="bold", color="purple200"),
            ft.Container(
                content=ft.Row([
                    ft.Column([ft.Text("Ingresos", size=11, color="grey400"), txt_ingresos], expand=True),
                    ft.Column([ft.Text("Gastos", size=11, color="grey400"), txt_gastos], expand=True),
                ]),
                bgcolor="#1e1e26", padding=20, border_radius=20
            ),
            ft.Text("Movimientos Recientes", size=16, weight="w500"),
            lista_movimientos
        ], expand=True)
    )

    def run_timer():
        while True:
            actualizar_lista()
            time.sleep(10) # 10 segundos para no saturar el servidor gratuito

    thread = threading.Thread(target=run_timer, daemon=True)
    thread.start()
    # Ejecución inicial
    actualizar_lista()

if __name__ == "__main__":
    ft.app(target=main)
