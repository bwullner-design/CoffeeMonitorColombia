
# ☕ CoffeeMonitor Colombia

**Plataforma de inteligencia de mercado para el sector cafetero colombiano.**

Recopila, valida, almacena y analiza automáticamente información pública del mercado del café en Colombia.

## Versión 0.1.0 — MVP

### Funcionalidades

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| Base de datos | ✅ | SQLite con esquema completo (6 tablas + índices) |
| Scraper FNC | ✅ | Captura precio interno, Bolsa NY, TRM |
| Scraper TRM | ✅ | API Datos Abiertos Colombia (datos.gov.co) |
| Scraper Cooperativas | ✅ | Framework con parsers por cooperativa |
| Validación | ✅ | Rangos, fechas, campos obligatorios |
| Motor de reglas | ✅ | R001-R005 con alertas configurables |
| Exportación | ✅ | Excel (mercado, ranking, alertas) + CSV |
| Dashboard consola | ✅ | Resumen visual en terminal |
| Dashboard PySide6 | 🔜 v0.3 | Interfaz gráfica |

### Fuentes de datos

- **FNC** — Precio interno diario (federaciondecafeteros.org)
- **Banco de la República** — TRM oficial (datos.gov.co/resource/32sa-8pi3)
- **Cooperativas** — Precios diarios de compra:
  - Cooperativa de Caficultores de Antioquia
  - COOCAFISA (Salgar)
  - Cooperativa del Occidente de Antioquia
  - Cooperacafé (Catatumbo)
  - Cooperativa de Andes

## Instalación

```bash
# Clonar o copiar el proyecto
cd CoffeeMonitorColombia

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos
python main.py --init
```

## Uso

```bash
# Captura completa (FNC + TRM + Cooperativas + Reglas)
python main.py --capture

# Capturar solo FNC
python main.py --capture fnc

# Capturar solo TRM
python main.py --capture trm

# Importar TRM histórica
python main.py --import-trm 2024-01-01 2024-12-31

# Ver estado del sistema
python main.py --status

# Dashboard en consola
python main.py --dashboard

# Exportar datos de mercado a Excel
python main.py --export market 2024-01-01 2024-06-30

# Exportar ranking de cooperativas
python main.py --export ranking 2024-07-08

# Exportar alertas activas
python main.py --export alerts

# Exportar a CSV
python main.py --export csv 2024-01-01 2024-06-30

# Modo verbose
python main.py --capture -v
```

## Tests

```bash
python -m pytest tests/ -v
# o
python tests/test_core.py
```

## Arquitectura

```
Internet → Capture Engine → Validation Engine → SQLite → Rules Engine → Dashboard / Export
```

Cada módulo tiene **una sola responsabilidad**:
- **Capture Engine**: solo descarga información
- **Validation Engine**: solo verifica integridad
- **Database**: solo persiste datos
- **Rules Engine**: solo evalúa reglas y genera alertas
- **Dashboard**: solo visualiza
- **Export Engine**: solo genera archivos

## Estructura del proyecto

```
CoffeeMonitorColombia/
├── main.py                 # Punto de entrada CLI
├── requirements.txt
├── config/
│   └── settings.py         # Configuración central
├── database/
│   ├── connection.py       # Gestión de conexión SQLite
│   └── schema.py           # DDL + seeds
├── repositories/
│   ├── market_repo.py      # CRUD mercado (FNC, NY, TRM)
│   ├── price_repo.py       # CRUD precios cooperativas
│   ├── alerts_repo.py      # CRUD alertas
│   └── sources_repo.py     # CRUD fuentes + log de captura
├── scrapers/
│   ├── base_scraper.py     # Clase base con reintentos
│   ├── fnc_scraper.py      # Scraper FNC
│   ├── trm_scraper.py      # Scraper TRM (API SODA)
│   └── coop_scraper.py     # Framework cooperativas
├── services/
│   ├── capture_service.py  # Orquestación de captura
│   ├── validation_service.py
│   ├── rules_service.py    # Motor de reglas R001-R005
│   └── export_service.py   # Excel + CSV
├── tests/
│   └── test_core.py
├── data/                   # Base de datos SQLite
├── exports/                # Archivos exportados
└── logs/                   # Logs del sistema
```

## Principios

1. Keep it Simple
2. Reliability First
3. Automate Everything
4. One Source of Truth
5. Nunca borrar históricos
6. Código limpio y mantenible
7. Cada módulo tiene una sola responsabilidad
8. Cada nueva funcionalidad debe aportar valor real

## Roadmap

- [x] **v0.1** — Base de datos + Scrapers + Validación + Reglas + Export
- [ ] **v0.2** — Captura automática programada (schedule)
- [ ] **v0.3** — Dashboard PySide6
- [ ] **v0.4** — 10+ cooperativas
- [ ] **v0.5** — Motor de reglas avanzado
- [ ] **v1.0** — Plataforma estable para uso diario

---

*Green Coffee Company — Inteligencia de Mercado Cafetero*
=======
# CoffeeMonitorColombia
Sistema de Inteligencia del Mercado Cafetero Colombiano
>>>>>>> d93f6a591bfc97208a408890a9e80c5877f23bc3
