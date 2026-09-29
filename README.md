# Movimientos Nequi y Nu

Aplicación móvil desarrollada con [Flet](https://flet.dev/) para visualizar movimientos de ingresos en tiempo real de Nequi y Nu.

## Características

- Visualización de ingresos de Nequi y Nu
- Filtros por banco
- Totales diarios y mensuales
- Actualización automática cada 10 segundos
- Interfaz moderna y responsive

## Requisitos

- Python 3.10 o superior
- Flet 1.0.1
- Requests 2.34.2

## Instalación Local

```bash
pip install -r requirements.txt
# o
pip install flet==1.0.1 requests==2.34.2
```

## Ejecución

```bash
python main.py
```

## Construcción del APK

### Construcción Automática (GitHub Actions)

El repositorio incluye un workflow de GitHub Actions que construye automáticamente el APK cuando se hace push a la rama `main` o se crea un pull request.

**Proceso de construcción:**

1. Configura el entorno con Python 3.12 y Java 17
2. Instala Flutter 3.44.8 (versión requerida por Flet 1.0.1)
3. Instala Flet CLI y sus dependencias
4. Ejecuta los tests unitarios
5. Construye el APK con `flet build apk --yes`
6. Sube el APK como artefacto

**Descargar el APK:**

1. Ve a la pestaña "Actions" del repositorio en GitHub
2. Selecciona el workflow "Build APK" más reciente
3. Descarga el artefacto `app-release` que contiene el APK
4. Instala el APK en tu dispositivo Android

### Construcción Manual

Para construir el APK manualmente en tu máquina:

```bash
# Instalar Flet CLI
pip install "flet[cli]==1.0.1"

# Construir el APK
flet build apk --yes
```

El APK se generará en `build/apk/`.

## Estructura del Proyecto

- `main.py` - Aplicación principal de Flet
- `parser.py` - Parser de notificaciones bancarias
- `api.py` - API Flask para webhooks
- `database.py` - Gestión de MongoDB
- `test_parser.py` - Tests unitarios
- `pyproject.toml` - Configuración del proyecto y Flet

## Configuración

La aplicación se conecta a la API en `https://nequi-lector.onrender.com/movimientos` para obtener los movimientos.

### Variables de entorno (para el servidor API)

- `MONGO_URI` - URI de conexión a MongoDB
- `WEBHOOK_TOKEN` - Token de autenticación para webhooks
- `PORT` - Puerto del servidor (por defecto 10000)

## Tecnologías

- **Flet 1.0.1** - Framework para aplicaciones multiplataforma con Python
- **Flutter 3.44.8** - Engine subyacente para la UI
- **Flask** - API backend para webhooks
- **MongoDB** - Base de datos para almacenar movimientos
- **GitHub Actions** - CI/CD para construcción automática del APK

## Licencia

Proyecto personal para gestión de movimientos bancarios.
