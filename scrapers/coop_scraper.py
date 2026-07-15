"""
CoffeeMonitor Colombia - Scraper de Cooperativas
==================================================
Framework genérico para capturar precios de cooperativas cafeteras.
Cada cooperativa tiene su propio parser porque la estructura HTML varía.
"""

import re
from datetime import datetime
from typing import Callable

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, CaptureResult
from scrapers.fnc_scraper import _parse_cop


class CoopScraper(BaseScraper):
    """Scraper genérico para cooperativas cafeteras."""

    # Registro de parsers por source_id
    _parsers: dict[str, Callable] = {}

    def __init__(self, source_id: str, nombre: str, url: str):
        super().__init__(source_id, nombre)
        self.url = url

    @classmethod
    def register_parser(cls, source_id: str):
        """Decorador para registrar un parser de cooperativa."""
        def decorator(func):
            cls._parsers[source_id] = func
            return func
        return decorator

    def _do_capture(self) -> CaptureResult:
        fecha = datetime.now().strftime("%Y-%m-%d")

        response = self._get(self.url)
        soup = BeautifulSoup(response.text, "lxml")

        # Si hay un parser específico registrado, usarlo
        parser = self._parsers.get(self.source_id, self._generic_parser)
        return parser(self, soup, fecha, response.text)

    def _generic_parser(self, soup: BeautifulSoup, fecha: str,
                        raw_html: str) -> CaptureResult:
        """Parser genérico: busca patrones comunes de precio de café."""
        text = soup.get_text(separator=" | ")
        data = {}

        # Patrón 1: "Factor 94" seguido de un precio
        factor_94 = re.search(
            r"Factor\s+94[^$]*\$\s*([\d.,]+)", text, re.IGNORECASE
        )
        if factor_94:
            precio = _parse_cop(factor_94.group(1))
            if precio:
                data["precio_carga"] = precio
                data["factor"] = 94

        # Patrón 2: "Precio" o "Precio del café" seguido de un valor
        if not data:
            precio_match = re.search(
                r"Precio(?:\s+del\s+caf[eé])?\s*[:\s]*\$\s*([\d.,]+)",
                text, re.IGNORECASE,
            )
            if precio_match:
                precio = _parse_cop(precio_match.group(1))
                if precio and precio > 100_000:  # Filtrar valores no válidos
                    data["precio_carga"] = precio
                    data["factor"] = 94

        # Buscar precios para otros factores
        for factor in [87, 88, 90, 92]:
            factor_match = re.search(
                rf"Factor\s+{factor}[^$]*\$\s*([\d.,]+)", text, re.IGNORECASE
            )
            if factor_match:
                precio = _parse_cop(factor_match.group(1))
                if precio:
                    data[f"precio_factor_{factor}"] = precio

        if not data:
            return CaptureResult(
                success=False,
                source_id=self.source_id,
                fecha=fecha,
                error=f"No se encontró precio en {self.url}",
                raw_response=text[:2000],
            )

        return CaptureResult(
            success=True,
            source_id=self.source_id,
            fecha=fecha,
            data=data,
        )


# ─────────────────────────────────────────────
# Parsers específicos por cooperativa
# ─────────────────────────────────────────────

@CoopScraper.register_parser("coocafisa")
def _parse_coocafisa(scraper: CoopScraper, soup: BeautifulSoup,
                     fecha: str, raw_html: str) -> CaptureResult:
    """Parser para COOCAFISA (Salgar). Publica precios por factor en la homepage."""
    text = soup.get_text(separator=" | ")
    data = {}

    # COOCAFISA muestra: Factor 94 $2.200.000* | Factor 90 $2.298.000* | etc.
    for factor in [94, 92, 90, 88, 87]:
        match = re.search(
            rf"Factor\s+{factor}[^$]*\$\s*([\d.,]+)", text, re.IGNORECASE
        )
        if match:
            precio = _parse_cop(match.group(1))
            if precio:
                if factor == 94 or "precio_carga" not in data:
                    data["precio_carga"] = precio
                    data["factor"] = factor
                data[f"precio_factor_{factor}"] = precio

    return CaptureResult(
        success=bool(data),
        source_id=scraper.source_id,
        fecha=fecha,
        data=data,
        error=None if data else "No se encontraron precios en COOCAFISA",
    )


@CoopScraper.register_parser("coop_antioquia")
def _parse_coop_antioquia(scraper: CoopScraper, soup: BeautifulSoup,
                          fecha: str, raw_html: str) -> CaptureResult:
    """Parser para Cooperativa de Caficultores de Antioquia."""
    text = soup.get_text(separator=" | ")
    data = {}

    # Buscar precio principal
    precio_match = re.search(
        r"Precio(?:\s+del)?\s+Caf[eé]\s*[|:]\s*(?:Factor\s+\d+\s*[|:])?\s*\$\s*([\d.,]+)",
        text, re.IGNORECASE,
    )
    if precio_match:
        precio = _parse_cop(precio_match.group(1))
        if precio:
            data["precio_carga"] = precio
            data["factor"] = 94

    # Fallback: parser genérico
    if not data:
        return scraper._generic_parser(soup, fecha, raw_html)

    return CaptureResult(
        success=bool(data),
        source_id=scraper.source_id,
        fecha=fecha,
        data=data,
    )


@CoopScraper.register_parser("coop_occidente")
def _parse_coop_occidente(scraper: CoopScraper, soup: BeautifulSoup,
                          fecha: str, raw_html: str) -> CaptureResult:
    """Parser para Cooperativa del Occidente de Antioquia."""
    # Tiene una página dedicada /precio-cafe/
    text = soup.get_text(separator=" | ")
    data = {}

    # Buscar tabla de precios por factor
    for factor in [94, 92, 90, 88, 87]:
        match = re.search(
            rf"(?:Factor|Fac\.?)\s*{factor}[^$]*\$\s*([\d.,]+)",
            text, re.IGNORECASE,
        )
        if match:
            precio = _parse_cop(match.group(1))
            if precio:
                if "precio_carga" not in data:
                    data["precio_carga"] = precio
                    data["factor"] = factor
                data[f"precio_factor_{factor}"] = precio

    if not data:
        return scraper._generic_parser(soup, fecha, raw_html)

    return CaptureResult(
        success=bool(data),
        source_id=scraper.source_id,
        fecha=fecha,
        data=data,
    )


def create_coop_scraper(source: dict) -> CoopScraper:
    """Factory: crea un CoopScraper a partir de la config de una fuente."""
    return CoopScraper(
        source_id=source["id"],
        nombre=source["nombre"],
        url=source.get("url_precio", source["url"]),
    )
