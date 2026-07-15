"""
CoffeeMonitor Colombia - Motor de Reglas
==========================================
Ejecuta reglas configurables y genera alertas.

Reglas implementadas:
  R001 - Precio cooperativa > Precio FNC + diferencial máximo
  R002 - TRM publicada ≠ TRM oficial (Banco de la República)
  R003 - Cooperativa no publicó precio
  R004 - Cambio inesperado en diferenciales
  R005 - Variación diaria excesiva en precio FNC
"""

import logging
from datetime import datetime

from config.settings import (
    ALERTA_DIFERENCIAL_MAX,
    ALERTA_TRM_TOLERANCIA,
    ALERTA_VARIACION_DIARIA_FNC_PCT,
)
from repositories.market_repo import market_repo
from repositories.price_repo import price_repo
from repositories.alerts_repo import alerts_repo
from repositories.sources_repo import sources_repo

logger = logging.getLogger(__name__)


class RulesService:
    """Ejecuta reglas de negocio y genera alertas."""

    def run_all(self, fecha: str):
        """Ejecuta todas las reglas para una fecha dada."""
        logger.info(f"Ejecutando reglas para {fecha}...")
        self.rule_r001_diferencial_max(fecha)
        self.rule_r003_sin_publicacion(fecha)
        self.rule_r005_variacion_diaria(fecha)
        logger.info(f"Reglas ejecutadas para {fecha}.")

    def rule_r001_diferencial_max(self, fecha: str):
        """R001: Precio cooperativa > Precio FNC + diferencial máximo."""
        market = market_repo.get_by_date(fecha)
        if not market or not market.get("precio_fnc"):
            return

        precio_fnc = market["precio_fnc"]
        precios = price_repo.get_by_date(fecha)

        for p in precios:
            diferencial = p["precio_carga"] - precio_fnc
            if diferencial > ALERTA_DIFERENCIAL_MAX:
                alerts_repo.insert(
                    fecha=fecha,
                    regla="R001",
                    severidad="warning",
                    source_id=p["source_id"],
                    mensaje=(
                        f"Diferencial alto: {p.get('cooperativa_nombre', p['source_id'])} "
                        f"paga COP {diferencial:,.0f} sobre FNC "
                        f"(límite: COP {ALERTA_DIFERENCIAL_MAX:,.0f})"
                    ),
                    valor_actual=diferencial,
                    valor_referencia=ALERTA_DIFERENCIAL_MAX,
                )

    def rule_r002_trm_discrepancia(self, fecha: str, trm_fuente: float, trm_oficial: float):
        """R002: TRM publicada por una fuente ≠ TRM oficial del Banco de la República."""
        diferencia = abs(trm_fuente - trm_oficial)
        if diferencia > ALERTA_TRM_TOLERANCIA:
            alerts_repo.insert(
                fecha=fecha,
                regla="R002",
                severidad="warning",
                mensaje=(
                    f"Discrepancia TRM: fuente reporta ${trm_fuente:,.2f}, "
                    f"oficial es ${trm_oficial:,.2f} "
                    f"(diferencia: ${diferencia:,.2f})"
                ),
                valor_actual=trm_fuente,
                valor_referencia=trm_oficial,
            )

    def rule_r003_sin_publicacion(self, fecha: str):
        """R003: Una cooperativa activa no publicó precio."""
        cooperativas = sources_repo.get_cooperativas()
        precios_del_dia = price_repo.get_by_date(fecha)
        fuentes_con_precio = {p["source_id"] for p in precios_del_dia}

        # Solo alertar en días hábiles (lunes a viernes)
        dt = datetime.strptime(fecha, "%Y-%m-%d")
        if dt.weekday() >= 5:  # Sábado o domingo
            return

        for coop in cooperativas:
            if coop["id"] not in fuentes_con_precio:
                alerts_repo.insert(
                    fecha=fecha,
                    regla="R003",
                    severidad="info",
                    source_id=coop["id"],
                    mensaje=f"Sin precio publicado: {coop['nombre']}",
                )

    def rule_r005_variacion_diaria(self, fecha: str):
        """R005: Variación diaria excesiva en precio FNC."""
        market_hoy = market_repo.get_by_date(fecha)
        if not market_hoy or not market_hoy.get("precio_fnc"):
            return

        market_ayer = market_repo.get_previous(fecha)
        if not market_ayer or not market_ayer.get("precio_fnc"):
            return

        precio_hoy = market_hoy["precio_fnc"]
        precio_ayer = market_ayer["precio_fnc"]

        if precio_ayer == 0:
            return

        variacion_pct = abs((precio_hoy - precio_ayer) / precio_ayer) * 100

        if variacion_pct > ALERTA_VARIACION_DIARIA_FNC_PCT:
            direction = "subió" if precio_hoy > precio_ayer else "bajó"
            alerts_repo.insert(
                fecha=fecha,
                regla="R005",
                severidad="critical" if variacion_pct > 20 else "warning",
                mensaje=(
                    f"Variación diaria excesiva: precio FNC {direction} "
                    f"{variacion_pct:.1f}% "
                    f"(${precio_ayer:,.0f} → ${precio_hoy:,.0f})"
                ),
                valor_actual=variacion_pct,
                valor_referencia=ALERTA_VARIACION_DIARIA_FNC_PCT,
            )


rules_service = RulesService()
