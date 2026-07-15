"""
CoffeeMonitor Colombia - Motor de Validación
==============================================
Verifica la integridad de los datos antes de guardarlos.
Campos obligatorios, rangos válidos, fechas, duplicados.
"""

import logging
from datetime import datetime
from dataclasses import dataclass

from config.settings import (
    PRECIO_FNC_MIN, PRECIO_FNC_MAX,
    BOLSA_NY_MIN, BOLSA_NY_MAX,
    TRM_MIN, TRM_MAX,
    PRECIO_COOP_MIN, PRECIO_COOP_MAX,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]

    @staticmethod
    def ok():
        return ValidationResult(valid=True, errors=[], warnings=[])

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str):
        self.warnings.append(msg)


class ValidationService:
    """Valida datos capturados antes de persistirlos."""

    def validate_fecha(self, fecha: str) -> ValidationResult:
        """Valida que la fecha sea correcta y no futura."""
        result = ValidationResult.ok()
        try:
            dt = datetime.strptime(fecha, "%Y-%m-%d")
            if dt.date() > datetime.now().date():
                result.add_error(f"Fecha futura no permitida: {fecha}")
            if dt.year < 2000:
                result.add_warning(f"Fecha muy antigua: {fecha}")
        except ValueError:
            result.add_error(f"Formato de fecha inválido: {fecha} (esperado YYYY-MM-DD)")
        return result

    def validate_market_data(self, data: dict) -> ValidationResult:
        """Valida datos de mercado (FNC, Bolsa NY, TRM)."""
        result = ValidationResult.ok()

        precio_fnc = data.get("precio_fnc")
        if precio_fnc is not None:
            if not isinstance(precio_fnc, (int, float)):
                result.add_error(f"precio_fnc no es numérico: {precio_fnc}")
            elif precio_fnc < PRECIO_FNC_MIN or precio_fnc > PRECIO_FNC_MAX:
                result.add_error(
                    f"precio_fnc fuera de rango: {precio_fnc:,.0f} "
                    f"(esperado {PRECIO_FNC_MIN:,}-{PRECIO_FNC_MAX:,})"
                )

        bolsa_ny = data.get("bolsa_ny")
        if bolsa_ny is not None:
            if not isinstance(bolsa_ny, (int, float)):
                result.add_error(f"bolsa_ny no es numérico: {bolsa_ny}")
            elif bolsa_ny < BOLSA_NY_MIN or bolsa_ny > BOLSA_NY_MAX:
                result.add_error(
                    f"bolsa_ny fuera de rango: {bolsa_ny:.2f} "
                    f"(esperado {BOLSA_NY_MIN}-{BOLSA_NY_MAX})"
                )

        trm = data.get("trm")
        if trm is not None:
            if not isinstance(trm, (int, float)):
                result.add_error(f"trm no es numérico: {trm}")
            elif trm < TRM_MIN or trm > TRM_MAX:
                result.add_error(
                    f"trm fuera de rango: {trm:,.2f} "
                    f"(esperado {TRM_MIN:,}-{TRM_MAX:,})"
                )

        # Al menos un campo debe tener datos
        if all(data.get(k) is None for k in ["precio_fnc", "bolsa_ny", "trm"]):
            result.add_error("No hay datos de mercado (todos los campos son None)")

        return result

    def validate_price_data(self, data: dict) -> ValidationResult:
        """Valida datos de precio de cooperativa."""
        result = ValidationResult.ok()

        precio = data.get("precio_carga")
        if precio is None:
            result.add_error("precio_carga es obligatorio")
        elif not isinstance(precio, (int, float)):
            result.add_error(f"precio_carga no es numérico: {precio}")
        elif precio < PRECIO_COOP_MIN or precio > PRECIO_COOP_MAX:
            result.add_error(
                f"precio_carga fuera de rango: {precio:,.0f} "
                f"(esperado {PRECIO_COOP_MIN:,}-{PRECIO_COOP_MAX:,})"
            )

        factor = data.get("factor", 94)
        if factor not in range(80, 100):
            result.add_warning(f"Factor de rendimiento inusual: {factor}")

        return result


validation_service = ValidationService()
