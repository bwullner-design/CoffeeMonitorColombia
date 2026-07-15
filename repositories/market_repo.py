"""
CoffeeMonitor Colombia - Repositorio de Datos de Mercado
=========================================================
CRUD para market_snapshot (FNC, Bolsa NY, TRM).
Principio: Solo INSERT. Nunca UPDATE ni DELETE en datos históricos.
"""

import logging
from typing import Optional
from database.connection import db

logger = logging.getLogger(__name__)


class MarketRepository:

    def insert(self, fecha: str, precio_fnc: float = None,
               bolsa_ny: float = None, trm: float = None,
               fuente: str = "fnc") -> bool:
        """Inserta un snapshot de mercado. Ignora duplicados."""
        try:
            with db.transaction() as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO market_snapshot
                       (fecha, precio_fnc, bolsa_ny, trm, fuente)
                       VALUES (?, ?, ?, ?, ?)""",
                    (fecha, precio_fnc, bolsa_ny, trm, fuente),
                )
            logger.debug(f"Market snapshot insertado: {fecha}")
            return True
        except Exception as e:
            logger.error(f"Error insertando market snapshot {fecha}: {e}")
            return False

    def get_by_date(self, fecha: str) -> Optional[dict]:
        """Obtiene el snapshot de mercado para una fecha."""
        with db.cursor() as cur:
            cur.execute(
                "SELECT * FROM market_snapshot WHERE fecha = ? ORDER BY captured_at DESC LIMIT 1",
                (fecha,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_latest(self) -> Optional[dict]:
        """Obtiene el snapshot más reciente."""
        with db.cursor() as cur:
            cur.execute(
                "SELECT * FROM market_snapshot ORDER BY fecha DESC, captured_at DESC LIMIT 1"
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_range(self, fecha_inicio: str, fecha_fin: str) -> list[dict]:
        """Obtiene snapshots en un rango de fechas."""
        with db.cursor() as cur:
            cur.execute(
                """SELECT * FROM market_snapshot
                   WHERE fecha BETWEEN ? AND ?
                   ORDER BY fecha ASC""",
                (fecha_inicio, fecha_fin),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_last_n_days(self, n: int = 30) -> list[dict]:
        """Obtiene los últimos N días de datos."""
        with db.cursor() as cur:
            cur.execute(
                """SELECT * FROM market_snapshot
                   ORDER BY fecha DESC
                   LIMIT ?""",
                (n,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_previous(self, fecha: str) -> Optional[dict]:
        """Obtiene el snapshot del día anterior a la fecha dada."""
        with db.cursor() as cur:
            cur.execute(
                """SELECT * FROM market_snapshot
                   WHERE fecha < ?
                   ORDER BY fecha DESC LIMIT 1""",
                (fecha,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def count(self) -> int:
        """Total de registros."""
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM market_snapshot")
            return cur.fetchone()["total"]


market_repo = MarketRepository()
