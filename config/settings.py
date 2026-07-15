"""
CoffeeMonitor Colombia - Configuración Central
================================================
Todos los parámetros configurables del sistema.
Nunca hardcodear valores en otros módulos.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────
# Rutas del proyecto
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXPORTS_DIR = BASE_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = DATA_DIR / "coffeemonitor.db"

# Crear directorios si no existen
for d in [DATA_DIR, EXPORTS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# Fuentes de datos
# ─────────────────────────────────────────────

# FNC - Federación Nacional de Cafeteros
FNC_PRICE_PDF_URL = (
    "https://federaciondecafeteros.org/wp-content/uploads/"
    "{year}/{month:02d}/precio_cafe.pdf"
)
FNC_BASE_URL = "https://federaciondecafeteros.org"
FNC_PUBLICATIONS_URL = f"{FNC_BASE_URL}/wp/publicaciones/"

# TRM - Tasa Representativa del Mercado (Datos Abiertos Colombia)
TRM_API_URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"

# Todoparacafe (fuente alternativa / validación cruzada)
TODOPARACAFE_URL = "https://www.todoparacafe.com/precio-cafe"

# ─────────────────────────────────────────────
# Cooperativas - Catálogo inicial (Antioquia)
# ─────────────────────────────────────────────
COOPERATIVAS = [
    {
        "id": "coop_antioquia",
        "nombre": "Cooperativa de Caficultores de Antioquia",
        "departamento": "Antioquia",
        "municipio": "Medellín",
        "url": "https://www.cafedeantioquia.com/",
        "url_precio": "https://www.cafedeantioquia.com/",
        "metodo": "html",
    },
    {
        "id": "coocafisa",
        "nombre": "Cooperativa de Caficultores de Salgar (COOCAFISA)",
        "departamento": "Antioquia",
        "municipio": "Salgar",
        "url": "https://coocafisa.com/",
        "url_precio": "https://coocafisa.com/",
        "metodo": "html",
    },
    {
        "id": "coop_occidente",
        "nombre": "Cooperativa de Caficultores del Occidente de Antioquia",
        "departamento": "Antioquia",
        "municipio": "Medellín",
        "url": "https://coopeoccidente.com.co/",
        "url_precio": "https://coopeoccidente.com.co/precio-cafe/",
        "metodo": "html",
    },
    {
        "id": "cooperacafe",
        "nombre": "Cooperativa de Caficultores del Catatumbo (Cooperacafé)",
        "departamento": "Norte de Santander",
        "municipio": "Ocaña",
        "url": "https://cooperacafe.com/",
        "url_precio": "https://cooperacafe.com/",
        "metodo": "html",
    },
    {
        "id": "coop_andes",
        "nombre": "Cooperativa de Caficultores de Andes",
        "departamento": "Antioquia",
        "municipio": "Andes",
        "url": "https://coopcaficultoresandes.com/",
        "url_precio": "https://coopcaficultoresandes.com/",
        "metodo": "html",
    },
]

# ─────────────────────────────────────────────
# Parámetros de validación
# ─────────────────────────────────────────────

# Precio FNC: rango válido en COP por carga de 125 kg
PRECIO_FNC_MIN = 500_000
PRECIO_FNC_MAX = 5_000_000

# Bolsa NY: rango válido en centavos de dólar por libra
BOLSA_NY_MIN = 50.0
BOLSA_NY_MAX = 600.0

# TRM: rango válido en COP por USD
TRM_MIN = 2_500.0
TRM_MAX = 6_000.0

# Precio cooperativa: rango válido en COP por carga
PRECIO_COOP_MIN = 400_000
PRECIO_COOP_MAX = 5_500_000

# ─────────────────────────────────────────────
# Reglas del motor de alertas
# ─────────────────────────────────────────────

# R001: Diferencial máximo cooperativa vs FNC (COP)
ALERTA_DIFERENCIAL_MAX = 35_000

# R002: Tolerancia TRM (COP)
ALERTA_TRM_TOLERANCIA = 5.0

# R004: Variación máxima permitida en diferenciales (%)
ALERTA_VARIACION_DIFERENCIAL_PCT = 15.0

# Variación diaria máxima permitida precio FNC (%)
ALERTA_VARIACION_DIARIA_FNC_PCT = 10.0

# ─────────────────────────────────────────────
# Scraping
# ─────────────────────────────────────────────
REQUEST_TIMEOUT = 30  # segundos
REQUEST_HEADERS = {
    "User-Agent": (
        "CoffeeMonitorColombia/0.1 "
        "(Market Intelligence; contact@greencoffeecompany.com)"
    ),
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}
MAX_RETRIES = 3
RETRY_DELAY = 5  # segundos entre reintentos

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE = LOGS_DIR / "coffeemonitor.log"

# ─────────────────────────────────────────────
# Exportación
# ─────────────────────────────────────────────
EXPORT_DATE_FORMAT = "%Y-%m-%d"
EXPORT_EXCEL_SHEET_MARKET = "Mercado"
EXPORT_EXCEL_SHEET_COOPS = "Cooperativas"
EXPORT_EXCEL_SHEET_ALERTS = "Alertas"
