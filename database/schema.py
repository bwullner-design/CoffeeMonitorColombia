"""
CoffeeMonitor Colombia - Esquema de Base de Datos
===================================================
Define y crea todas las tablas del sistema.
Principio: Nunca borrar históricos. Solo INSERT, nunca UPDATE en datos de mercado.
"""

import logging
from database.connection import db

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

TABLES = {
    "schema_version": """
        CREATE TABLE IF NOT EXISTS schema_version (
            version     INTEGER PRIMARY KEY,
            applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """,

    "sources": """
        CREATE TABLE IF NOT EXISTS sources (
            id              TEXT PRIMARY KEY,
            nombre          TEXT NOT NULL,
            tipo            TEXT NOT NULL CHECK (tipo IN ('fnc', 'cooperativa', 'exportador', 'oficial', 'bolsa')),
            departamento    TEXT,
            municipio       TEXT,
            sitio_web       TEXT,
            url_precio      TEXT,
            metodo_captura  TEXT CHECK (metodo_captura IN ('html', 'pdf', 'api', 'excel', 'manual')),
            activa          INTEGER NOT NULL DEFAULT 1,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """,

    "market_snapshot": """
        CREATE TABLE IF NOT EXISTS market_snapshot (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT NOT NULL,
            precio_fnc  REAL,
            bolsa_ny    REAL,
            trm         REAL,
            fuente      TEXT NOT NULL DEFAULT 'fnc',
            captured_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(fecha, fuente)
        )
    """,

    "price_snapshot": """
        CREATE TABLE IF NOT EXISTS price_snapshot (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha           TEXT NOT NULL,
            source_id       TEXT NOT NULL,
            precio_carga    REAL,
            factor          INTEGER DEFAULT 94,
            observaciones   TEXT,
            captured_at     TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (source_id) REFERENCES sources(id),
            UNIQUE(fecha, source_id, factor)
        )
    """,

    "premium_types": """
        CREATE TABLE IF NOT EXISTS premium_types (
            id          TEXT PRIMARY KEY,
            nombre      TEXT NOT NULL,
            descripcion TEXT,
            activo      INTEGER NOT NULL DEFAULT 1
        )
    """,

    "price_premiums": """
        CREATE TABLE IF NOT EXISTS price_premiums (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha           TEXT NOT NULL,
            source_id       TEXT NOT NULL,
            premium_type_id TEXT NOT NULL,
            valor           REAL NOT NULL,
            moneda          TEXT NOT NULL DEFAULT 'COP',
            captured_at     TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (source_id) REFERENCES sources(id),
            FOREIGN KEY (premium_type_id) REFERENCES premium_types(id),
            UNIQUE(fecha, source_id, premium_type_id)
        )
    """,

    "alerts": """
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT NOT NULL,
            regla       TEXT NOT NULL,
            severidad   TEXT NOT NULL DEFAULT 'info' CHECK (severidad IN ('info', 'warning', 'critical')),
            source_id   TEXT,
            mensaje     TEXT NOT NULL,
            valor_actual    REAL,
            valor_referencia REAL,
            resuelta    INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (source_id) REFERENCES sources(id)
        )
    """,

    "capture_log": """
        CREATE TABLE IF NOT EXISTS capture_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT NOT NULL,
            source_id   TEXT NOT NULL,
            status      TEXT NOT NULL CHECK (status IN ('success', 'error', 'no_data', 'skipped')),
            mensaje     TEXT,
            duration_ms INTEGER,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (source_id) REFERENCES sources(id)
        )
    """,
}

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_market_fecha ON market_snapshot(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_price_fecha ON price_snapshot(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_price_source ON price_snapshot(source_id)",
    "CREATE INDEX IF NOT EXISTS idx_price_fecha_source ON price_snapshot(fecha, source_id)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_fecha ON alerts(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_regla ON alerts(regla)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_resuelta ON alerts(resuelta)",
    "CREATE INDEX IF NOT EXISTS idx_capture_log_fecha ON capture_log(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_premiums_fecha ON price_premiums(fecha)",
]

# Datos iniciales para premium_types
DEFAULT_PREMIUM_TYPES = [
    ("fairtrade", "Fairtrade", "Certificación de comercio justo"),
    ("organico", "Orgánico", "Certificación orgánica (USDA, EU, JAS)"),
    ("rainforest", "Rainforest Alliance", "Certificación Rainforest Alliance"),
    ("utz", "UTZ", "Certificación UTZ (ahora parte de Rainforest)"),
    ("aaa", "AAA Nespresso", "Programa AAA de Nespresso"),
    ("4c", "4C", "Certificación 4C (Common Code for Coffee Community)"),
    ("cup_excellence", "Cup of Excellence", "Subasta Cup of Excellence"),
    ("specialty", "Especialidad", "Café de especialidad (SCA 80+)"),
    ("regional", "Denominación Regional", "Bonificación por origen regional"),
]


def initialize_database():
    """Crea todas las tablas e índices si no existen."""
    logger.info("Inicializando base de datos...")

    with db.transaction() as conn:
        # Crear tablas
        for name, sql in TABLES.items():
            conn.execute(sql)
            logger.debug(f"Tabla '{name}' verificada.")

        # Crear índices
        for idx_sql in INDEXES:
            conn.execute(idx_sql)

        # Insertar premium_types por defecto
        conn.executemany(
            """INSERT OR IGNORE INTO premium_types (id, nombre, descripcion)
               VALUES (?, ?, ?)""",
            DEFAULT_PREMIUM_TYPES,
        )

        # Registrar versión del esquema
        conn.execute(
            "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
            (SCHEMA_VERSION,),
        )

    logger.info(f"Base de datos inicializada (esquema v{SCHEMA_VERSION}).")


def seed_sources(sources_list: list[dict]):
    """Carga el catálogo de fuentes desde la configuración."""
    with db.transaction() as conn:
        for src in sources_list:
            conn.execute(
                """INSERT OR IGNORE INTO sources
                   (id, nombre, tipo, departamento, municipio, sitio_web, url_precio, metodo_captura)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    src["id"],
                    src["nombre"],
                    "cooperativa",
                    src.get("departamento"),
                    src.get("municipio"),
                    src.get("url"),
                    src.get("url_precio"),
                    src.get("metodo", "html"),
                ),
            )
        # Fuentes fijas del sistema
        conn.execute(
            """INSERT OR IGNORE INTO sources
               (id, nombre, tipo, sitio_web, metodo_captura)
               VALUES ('fnc', 'Federación Nacional de Cafeteros', 'fnc',
                        'https://federaciondecafeteros.org', 'pdf')"""
        )
        conn.execute(
            """INSERT OR IGNORE INTO sources
               (id, nombre, tipo, sitio_web, metodo_captura)
               VALUES ('banrep', 'Banco de la República', 'oficial',
                        'https://www.banrep.gov.co', 'api')"""
        )
        conn.execute(
            """INSERT OR IGNORE INTO sources
               (id, nombre, tipo, sitio_web, metodo_captura)
               VALUES ('ice_ny', 'ICE - Bolsa de Nueva York', 'bolsa',
                        'https://www.theice.com', 'api')"""
        )

    logger.info(f"Catálogo de fuentes cargado ({len(sources_list)} cooperativas + 3 fuentes fijas).")
