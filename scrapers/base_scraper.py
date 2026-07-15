"""
CoffeeMonitor Colombia - Scraper Base
=======================================
Clase base para todos los scrapers.
Responsabilidad: Solo obtener información. No guarda. No calcula.
"""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any

import requests

from config.settings import REQUEST_TIMEOUT, REQUEST_HEADERS, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)


@dataclass
class CaptureResult:
    """Resultado estandarizado de una captura."""
    success: bool
    source_id: str
    fecha: str
    data: dict = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: int = 0
    raw_response: Optional[str] = None


class BaseScraper(ABC):
    """Clase base para todos los scrapers del sistema."""

    def __init__(self, source_id: str, source_name: str):
        self.source_id = source_id
        self.source_name = source_name
        self.session = requests.Session()
        self.session.headers.update(REQUEST_HEADERS)
        self.logger = logging.getLogger(f"scraper.{source_id}")

    def _get(self, url: str, params: dict = None, **kwargs) -> requests.Response:
        """GET con reintentos automáticos."""
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    url, params=params, timeout=REQUEST_TIMEOUT, **kwargs
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                last_error = e
                self.logger.warning(
                    f"Intento {attempt}/{MAX_RETRIES} fallido para {url}: {e}"
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)

        raise last_error

    def capture(self) -> CaptureResult:
        """Ejecuta la captura con medición de tiempo."""
        start = time.time()
        try:
            result = self._do_capture()
            result.duration_ms = int((time.time() - start) * 1000)
            if result.success:
                self.logger.info(
                    f"Captura exitosa [{self.source_name}] "
                    f"({result.duration_ms}ms): {result.data}"
                )
            return result
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self.logger.error(f"Error capturando [{self.source_name}]: {e}")
            return CaptureResult(
                success=False,
                source_id=self.source_id,
                fecha=datetime.now().strftime("%Y-%m-%d"),
                error=str(e),
                duration_ms=duration,
            )

    @abstractmethod
    def _do_capture(self) -> CaptureResult:
        """Implementar en cada scraper concreto."""
        ...
