"""
CoffeeMonitor Colombia - Conexión a Base de Datos
===================================================
Maneja la conexión SQLite con soporte para migración futura a PostgreSQL.
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path

from config.settings import DB_PATH

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Gestiona la conexión SQLite.

    Principio: Una sola fuente de verdad para la conexión.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_directory()

    def _ensure_directory(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Retorna una conexión con Row factory habilitado."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def transaction(self):
        """Context manager para transacciones con commit/rollback automático."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción: {e}")
            raise
        finally:
            conn.close()

    @contextmanager
    def cursor(self):
        """Context manager para operaciones de solo lectura."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            yield cur
        finally:
            conn.close()


# Instancia global
db = DatabaseConnection()
