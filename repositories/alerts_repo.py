"""
CoffeeMonitor Colombia - Repositorio de Alertas
=================================================
"""

import logging
from database.connection import db

logger = logging.getLogger(__name__)


class AlertsRepository:

    def insert(self, fecha: str, regla: str, mensaje: str,
               severidad: str = "warning", source_id: str = None,
               valor_actual: float = None, valor_referencia: float = None) -> bool:
        try:
            with db.transaction() as conn:
                conn.execute(
                    """INSERT INTO alerts
                       (fecha, regla, severidad, source_id, mensaje,
                        valor_actual, valor_referencia)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (fecha, regla, severidad, source_id, mensaje,
                     valor_actual, valor_referencia),
                )
            logger.info(f"Alerta [{regla}] {severidad}: {mensaje}")
            return True
        except Exception as e:
            logger.error(f"Error insertando alerta: {e}")
            return False

    def get_active(self, limit: int = 50) -> list[dict]:
        """Alertas no resueltas, más recientes primero."""
        with db.cursor() as cur:
            cur.execute(
                """SELECT a.*, s.nombre as source_nombre
                   FROM alerts a
                   LEFT JOIN sources s ON a.source_id = s.id
                   WHERE a.resuelta = 0
                   ORDER BY a.created_at DESC LIMIT ?""",
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_by_date(self, fecha: str) -> list[dict]:
        with db.cursor() as cur:
            cur.execute(
                """SELECT a.*, s.nombre as source_nombre
                   FROM alerts a
                   LEFT JOIN sources s ON a.source_id = s.id
                   WHERE a.fecha = ?
                   ORDER BY a.severidad DESC""",
                (fecha,),
            )
            return [dict(row) for row in cur.fetchall()]

    def resolve(self, alert_id: int) -> bool:
        try:
            with db.transaction() as conn:
                conn.execute(
                    "UPDATE alerts SET resuelta = 1 WHERE id = ?",
                    (alert_id,),
                )
            return True
        except Exception as e:
            logger.error(f"Error resolviendo alerta {alert_id}: {e}")
            return False

    def get_by_rule(self, regla: str, limit: int = 20) -> list[dict]:
        with db.cursor() as cur:
            cur.execute(
                """SELECT * FROM alerts WHERE regla = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (regla, limit),
            )
            return [dict(row) for row in cur.fetchall()]

    def count_active(self) -> int:
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM alerts WHERE resuelta = 0")
            return cur.fetchone()["total"]


alerts_repo = AlertsRepository()
