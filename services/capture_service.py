"""
CoffeeMonitor Colombia - Servicio de Captura
==============================================
Orquesta todo el ciclo: capturar → validar → guardar → log.
"""

import logging
from datetime import datetime

from scrapers.fnc_scraper import FNCScraper
from scrapers.trm_scraper import TRMScraper
from scrapers.coop_scraper import create_coop_scraper
from services.validation_service import validation_service
from services.rules_service import rules_service
from repositories.market_repo import market_repo
from repositories.price_repo import price_repo
from repositories.sources_repo import sources_repo, capture_log_repo
from config.settings import COOPERATIVAS

logger = logging.getLogger(__name__)


class CaptureService:
    """Orquesta la captura de todas las fuentes."""

    def __init__(self):
        self.fnc_scraper = FNCScraper()
        self.trm_scraper = TRMScraper()

    def run_full_capture(self):
        """Ejecuta captura completa: FNC + TRM + Cooperativas + Reglas."""
        logger.info("=" * 60)
        logger.info("INICIO DE CAPTURA COMPLETA")
        logger.info("=" * 60)

        fecha = datetime.now().strftime("%Y-%m-%d")

        # 1. Capturar FNC (precio interno, bolsa NY, TRM)
        self.capture_fnc()

        # 2. Capturar TRM oficial (validación cruzada)
        self.capture_trm()

        # 3. Capturar cooperativas
        self.capture_cooperativas()

        # 4. Ejecutar reglas
        rules_service.run_all(fecha)

        logger.info("=" * 60)
        logger.info("CAPTURA COMPLETA FINALIZADA")
        logger.info("=" * 60)

    def capture_fnc(self) -> bool:
        """Captura datos de la FNC."""
        result = self.fnc_scraper.capture()

        if not result.success:
            capture_log_repo.log(
                result.fecha, "fnc", "error", result.error, result.duration_ms
            )
            return False

        # Validar fecha
        v_fecha = validation_service.validate_fecha(result.fecha)
        if not v_fecha.valid:
            capture_log_repo.log(
                result.fecha, "fnc", "error",
                f"Validación de fecha: {v_fecha.errors}", result.duration_ms,
            )
            return False

        # Validar datos de mercado
        v_data = validation_service.validate_market_data(result.data)
        if not v_data.valid:
            capture_log_repo.log(
                result.fecha, "fnc", "error",
                f"Validación de datos: {v_data.errors}", result.duration_ms,
            )
            return False

        for w in v_data.warnings:
            logger.warning(f"FNC advertencia: {w}")

        # Guardar
        market_repo.insert(
            fecha=result.fecha,
            precio_fnc=result.data.get("precio_fnc"),
            bolsa_ny=result.data.get("bolsa_ny"),
            trm=result.data.get("trm"),
            fuente="fnc",
        )

        capture_log_repo.log(
            result.fecha, "fnc", "success",
            f"Datos: {result.data}", result.duration_ms,
        )
        return True

    def capture_trm(self) -> bool:
        """Captura TRM oficial del Banco de la República."""
        result = self.trm_scraper.capture()

        if not result.success:
            capture_log_repo.log(
                result.fecha, "banrep", "error", result.error, result.duration_ms
            )
            return False

        trm_value = result.data.get("trm")
        if trm_value:
            # Verificar si ya tenemos TRM de la FNC para validación cruzada
            market = market_repo.get_by_date(result.fecha)
            if market and market.get("trm"):
                rules_service.rule_r002_trm_discrepancia(
                    result.fecha, market["trm"], trm_value
                )

            # Actualizar o insertar con TRM oficial
            market_repo.insert(
                fecha=result.fecha,
                trm=trm_value,
                fuente="banrep",
            )

        capture_log_repo.log(
            result.fecha, "banrep", "success",
            f"TRM: {trm_value}", result.duration_ms,
        )
        return True

    def capture_cooperativas(self) -> dict[str, bool]:
        """Captura precios de todas las cooperativas activas."""
        results = {}

        for coop_config in COOPERATIVAS:
            source_id = coop_config["id"]
            try:
                scraper = create_coop_scraper(coop_config)
                result = scraper.capture()

                if result.success:
                    # Validar precio
                    v = validation_service.validate_price_data(result.data)
                    if v.valid:
                        price_repo.insert(
                            fecha=result.fecha,
                            source_id=source_id,
                            precio_carga=result.data["precio_carga"],
                            factor=result.data.get("factor", 94),
                        )
                        capture_log_repo.log(
                            result.fecha, source_id, "success",
                            f"Precio: {result.data}", result.duration_ms,
                        )
                        results[source_id] = True
                    else:
                        capture_log_repo.log(
                            result.fecha, source_id, "error",
                            f"Validación: {v.errors}", result.duration_ms,
                        )
                        results[source_id] = False
                else:
                    capture_log_repo.log(
                        result.fecha, source_id, "error",
                        result.error, result.duration_ms,
                    )
                    results[source_id] = False

            except Exception as e:
                logger.error(f"Error capturando {source_id}: {e}")
                capture_log_repo.log(
                    datetime.now().strftime("%Y-%m-%d"),
                    source_id, "error", str(e),
                )
                results[source_id] = False

        return results

    def import_trm_history(self, fecha_inicio: str, fecha_fin: str) -> int:
        """Importa TRM histórica para un rango de fechas."""
        results = self.trm_scraper.capture_range(fecha_inicio, fecha_fin)
        count = 0
        for r in results:
            if r.success:
                market_repo.insert(
                    fecha=r.fecha,
                    trm=r.data["trm"],
                    fuente="banrep",
                )
                count += 1
        logger.info(f"TRM histórica importada: {count} registros")
        return count


capture_service = CaptureService()
