"""
CoffeeMonitor Colombia - Repositorio de Precios de Cooperativas
=================================================================
CRUD para price_snapshot.
"""

import logging
from typing import Optional
from database.connection import db

logger = logging.getLogger(__name__)


class PriceRepository:

    def insert(self, fecha: str, source_id: str, precio_carga: float,
               factor: int = 94, observaciones: str = None) -> bool:
        """Inserta un precio de cooperativa. Ignora duplicados."""
        try:
            with db.transaction() as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO price_snapshot
                       (fecha, source_id, precio_carga, factor, observaciones)
                       VALUES (?, ?, ?, ?, ?)""",
                    (fecha, source_id, precio_carga, factor, observaciones),
                )
            logger.debug(f"Price snapshot insertado: {source_id} @ {fecha}")
            return True
        except Exception as e:
            logger.error(f"Error insertando price snapshot: {e}")
            return False

    def get_by_date(self, fecha: str) -> list[dict]:
        """Todos los precios de cooperativas para una fecha."""
        with db.cursor() as cur:
            cur.execute(
                """SELECT ps.*, s.nombre as cooperativa_nombre, s.departamento
                   FROM price_snapshot ps
                   JOIN sources s ON ps.source_id = s.id
                   WHERE ps.fecha = ?
                   ORDER BY ps.precio_carga DESC""",
                (fecha,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_by_source(self, source_id: str, limit: int = 30) -> list[dict]:
        """Últimos N precios de una cooperativa."""
        with db.cursor() as cur:
            cur.execute(
                """SELECT * FROM price_snapshot
                   WHERE source_id = ?
                   ORDER BY fecha DESC LIMIT ?""",
                (source_id, limit),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_ranking(self, fecha: str) -> list[dict]:
        """Ranking de cooperativas por precio para una fecha, con diferencial vs FNC."""
        with db.cursor() as cur:
            cur.execute(
                """SELECT
                       ps.source_id,
                       s.nombre as cooperativa,
                       s.departamento,
                       ps.precio_carga,
                       ps.factor,
                       ms.precio_fnc,
                       CASE WHEN ms.precio_fnc IS NOT NULL
                            THEN ps.precio_carga - ms.precio_fnc
                            ELSE NULL END as diferencial
                   FROM price_snapshot ps
                   JOIN sources s ON ps.source_id = s.id
                   LEFT JOIN market_snapshot ms ON ps.fecha = ms.fecha
                   WHERE ps.fecha = ?
                   ORDER BY ps.precio_carga DESC""",
                (fecha,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_latest_by_source(self, source_id: str) -> Optional[dict]:
        """Último precio registrado de una cooperativa."""
        with db.cursor() as cur:
            cur.execute(
                """SELECT * FROM price_snapshot
                   WHERE source_id = ?
                   ORDER BY fecha DESC LIMIT 1""",
                (source_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_range(self, fecha_inicio: str, fecha_fin: str,
                  source_id: str = None) -> list[dict]:
        """Precios en un rango de fechas, opcionalmente filtrado por fuente."""
        with db.cursor() as cur:
            if source_id:
                cur.execute(
                    """SELECT ps.*, s.nombre as cooperativa_nombre
                       FROM price_snapshot ps
                       JOIN sources s ON ps.source_id = s.id
                       WHERE ps.fecha BETWEEN ? AND ? AND ps.source_id = ?
                       ORDER BY ps.fecha ASC""",
                    (fecha_inicio, fecha_fin, source_id),
                )
            else:
                cur.execute(
                    """SELECT ps.*, s.nombre as cooperativa_nombre
                       FROM price_snapshot ps
                       JOIN sources s ON ps.source_id = s.id
                       WHERE ps.fecha BETWEEN ? AND ?
                       ORDER BY ps.fecha ASC, ps.precio_carga DESC""",
                    (fecha_inicio, fecha_fin),
                )
            return [dict(row) for row in cur.fetchall()]


price_repo = PriceRepository()
