"""
CoffeeMonitor Colombia - Repositorio de Fuentes y Log de Captura
==================================================================
"""

import logging
from typing import Optional
from database.connection import db

logger = logging.getLogger(__name__)


class SourcesRepository:

    def get_all_active(self) -> list[dict]:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM sources WHERE activa = 1 ORDER BY tipo, nombre")
            return [dict(row) for row in cur.fetchall()]

    def get_cooperativas(self) -> list[dict]:
        with db.cursor() as cur:
            cur.execute(
                "SELECT * FROM sources WHERE tipo = 'cooperativa' AND activa = 1 ORDER BY nombre"
            )
            return [dict(row) for row in cur.fetchall()]

    def get_by_id(self, source_id: str) -> Optional[dict]:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM sources WHERE id = ?", (source_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def set_active(self, source_id: str, activa: bool) -> bool:
        try:
            with db.transaction() as conn:
                conn.execute(
                    "UPDATE sources SET activa = ?, updated_at = datetime('now') WHERE id = ?",
                    (1 if activa else 0, source_id),
                )
            return True
        except Exception as e:
            logger.error(f"Error actualizando fuente {source_id}: {e}")
            return False


class CaptureLogRepository:

    def log(self, fecha: str, source_id: str, status: str,
            mensaje: str = None, duration_ms: int = None) -> bool:
        try:
            with db.transaction() as conn:
                conn.execute(
                    """INSERT INTO capture_log
                       (fecha, source_id, status, mensaje, duration_ms)
                       VALUES (?, ?, ?, ?, ?)""",
                    (fecha, source_id, status, mensaje, duration_ms),
                )
            return True
        except Exception as e:
            logger.error(f"Error en capture_log: {e}")
            return False

    def get_status(self, fecha: str) -> list[dict]:
        """Estado de captura de todas las fuentes para una fecha."""
        with db.cursor() as cur:
            cur.execute(
                """SELECT cl.*, s.nombre as source_nombre
                   FROM capture_log cl
                   JOIN sources s ON cl.source_id = s.id
                   WHERE cl.fecha = ?
                   ORDER BY cl.created_at DESC""",
                (fecha,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_latest_by_source(self, source_id: str) -> Optional[dict]:
        with db.cursor() as cur:
            cur.execute(
                """SELECT * FROM capture_log
                   WHERE source_id = ?
                   ORDER BY created_at DESC LIMIT 1""",
                (source_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


sources_repo = SourcesRepository()
capture_log_repo = CaptureLogRepository()
