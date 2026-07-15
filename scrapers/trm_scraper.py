"""
CoffeeMonitor Colombia - Scraper TRM
======================================
Captura la Tasa Representativa del Mercado desde Datos Abiertos Colombia.

Fuente: https://www.datos.gov.co/resource/32sa-8pi3.json
API Socrata (SODA) - No requiere autenticación para consultas básicas.
"""

from datetime import datetime, timedelta

from scrapers.base_scraper import BaseScraper, CaptureResult
from config.settings import TRM_API_URL


class TRMScraper(BaseScraper):
    """Scraper para la TRM oficial desde Datos Abiertos Colombia."""

    def __init__(self):
        super().__init__("banrep", "Banco de la República (TRM)")

    def _do_capture(self) -> CaptureResult:
        """Captura la TRM más reciente."""
        today = datetime.now()
        fecha_str = today.strftime("%Y-%m-%d")

        # La API SODA usa el campo 'vigenciadesde' para filtrar
        # Buscar TRM para hoy o los últimos 5 días (fines de semana no hay TRM)
        for days_back in range(5):
            target_date = today - timedelta(days=days_back)
            date_query = target_date.strftime("%Y-%m-%dT00:00:00.000")

            params = {
                "$where": f"vigenciadesde = '{date_query}'",
                "$limit": 1,
                "$order": "vigenciadesde DESC",
            }

            try:
                response = self._get(TRM_API_URL, params=params)
                data = response.json()

                if data and len(data) > 0:
                    record = data[0]
                    trm_value = float(record.get("valor", 0))
                    vigencia = record.get("vigenciadesde", "")[:10]

                    if trm_value > 0:
                        return CaptureResult(
                            success=True,
                            source_id=self.source_id,
                            fecha=vigencia,
                            data={"trm": trm_value, "vigencia": vigencia},
                        )
            except Exception as e:
                self.logger.warning(f"Error consultando TRM para {target_date}: {e}")
                continue

        return CaptureResult(
            success=False,
            source_id=self.source_id,
            fecha=fecha_str,
            error="No se encontró TRM en los últimos 5 días",
        )

    def capture_range(self, fecha_inicio: str, fecha_fin: str) -> list[CaptureResult]:
        """Captura TRM para un rango de fechas (para importación histórica)."""
        results = []

        params = {
            "$where": (
                f"vigenciadesde >= '{fecha_inicio}T00:00:00.000' "
                f"AND vigenciadesde <= '{fecha_fin}T00:00:00.000'"
            ),
            "$limit": 5000,
            "$order": "vigenciadesde ASC",
        }

        try:
            response = self._get(TRM_API_URL, params=params)
            data = response.json()

            for record in data:
                trm_value = float(record.get("valor", 0))
                vigencia = record.get("vigenciadesde", "")[:10]

                if trm_value > 0:
                    results.append(
                        CaptureResult(
                            success=True,
                            source_id=self.source_id,
                            fecha=vigencia,
                            data={"trm": trm_value},
                        )
                    )

            self.logger.info(f"TRM histórica: {len(results)} registros ({fecha_inicio} a {fecha_fin})")
        except Exception as e:
            self.logger.error(f"Error capturando TRM histórica: {e}")

        return results
