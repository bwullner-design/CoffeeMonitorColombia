"""
CoffeeMonitor Colombia - Scraper FNC
======================================
Captura el precio interno de referencia de la Federación Nacional de Cafeteros.

Fuentes:
  - PDF diario: federaciondecafeteros.org/wp-content/uploads/{year}/{month}/precio_cafe.pdf
  - Página principal: federaciondecafeteros.org (widget con precio, bolsa NY, TRM)
  - Todoparacafe.com (fuente alternativa para validación cruzada)
"""

import re
from datetime import datetime

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, CaptureResult
from config.settings import FNC_PUBLICATIONS_URL, TODOPARACAFE_URL

# Patrones regex para extraer datos del sitio FNC
RE_PRECIO_FNC = re.compile(r"\$\s*([\d.,]+)\s*(?:000)?", re.IGNORECASE)
RE_BOLSA_NY = re.compile(r"(\d{2,3}[.,]\d{1,2})", re.IGNORECASE)
RE_TRM = re.compile(r"\$\s*([\d.,]+)", re.IGNORECASE)
RE_FECHA = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _parse_cop(text: str) -> float | None:
    """Parsea un valor en COP como '2.205.000' o '2,205,000' a float."""
    if not text:
        return None
    # Remover símbolo $ y espacios
    cleaned = text.replace("$", "").replace(" ", "").strip()
    # Detectar formato: si tiene puntos como separador de miles
    if "." in cleaned and "," not in cleaned:
        # Contar puntos: si hay más de uno, son separadores de miles
        dot_count = cleaned.count(".")
        if dot_count > 1:
            # 2.205.000 → 2205000
            cleaned = cleaned.replace(".", "")
        else:
            # Un solo punto: verificar si es decimal o miles
            parts = cleaned.split(".")
            if len(parts[1]) == 3 and len(parts[0]) > 1:
                # 2.205 probablemente es 2205 (miles)
                # Pero 3671.75 es decimal
                # Heurística: si la parte decimal tiene exactamente 3 dígitos, es miles
                cleaned = cleaned.replace(".", "")
            # Si no, dejar como decimal (3671.75 → 3671.75)
    elif "," in cleaned and "." in cleaned:
        # 2,205,000.00 o 2.205.000,00
        if cleaned.rindex(",") > cleaned.rindex("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # Podría ser 2,205,000 (sin decimales)
        parts = cleaned.split(",")
        if all(len(p) == 3 for p in parts[1:]):
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


class FNCScraper(BaseScraper):
    """Scraper para la Federación Nacional de Cafeteros."""

    def __init__(self):
        super().__init__("fnc", "Federación Nacional de Cafeteros")

    def _do_capture(self) -> CaptureResult:
        """Intenta capturar de la página de publicaciones de la FNC."""
        return self._capture_from_website()

    def _capture_from_website(self) -> CaptureResult:
        """Captura desde el sitio web principal de la FNC."""
        response = self._get(FNC_PUBLICATIONS_URL)
        html = response.text
        soup = BeautifulSoup(html, "lxml")

        data = {}
        fecha = datetime.now().strftime("%Y-%m-%d")

        # Buscar el widget de precio en la página
        # La FNC muestra: Precio interno, Bolsa NY, TRM con sus fechas
        text = soup.get_text(separator=" | ")

        # Extraer fecha del precio
        fecha_match = RE_FECHA.search(text)
        if fecha_match:
            fecha = fecha_match.group(1)

        # Extraer precio interno de referencia
        # Buscar patrones como "Precio interno de referencia: $2.205.000"
        precio_pattern = re.search(
            r"Precio\s+interno\s+de\s+referencia\s*:\s*\$\s*([\d.,]+)",
            text, re.IGNORECASE,
        )
        if precio_pattern:
            data["precio_fnc"] = _parse_cop(precio_pattern.group(1))

        # Extraer Bolsa de NY
        bolsa_pattern = re.search(
            r"Bolsa\s+de\s+NY\s*:\s*([\d.,]+)",
            text, re.IGNORECASE,
        )
        if bolsa_pattern:
            val = bolsa_pattern.group(1).replace(",", ".")
            try:
                data["bolsa_ny"] = float(val)
            except ValueError:
                pass

        # Extraer TRM
        trm_pattern = re.search(
            r"Tasa\s+de\s+cambio\s*:\s*\$\s*([\d.,]+)",
            text, re.IGNORECASE,
        )
        if trm_pattern:
            data["trm"] = _parse_cop(trm_pattern.group(1))

        if not data:
            return CaptureResult(
                success=False,
                source_id=self.source_id,
                fecha=fecha,
                error="No se encontraron datos de precio en la página FNC",
                raw_response=text[:2000],
            )

        return CaptureResult(
            success=True,
            source_id=self.source_id,
            fecha=fecha,
            data=data,
        )

    def capture_from_todoparacafe(self) -> CaptureResult:
        """Fuente alternativa: todoparacafe.com (validación cruzada)."""
        try:
            response = self._get(TODOPARACAFE_URL)
            soup = BeautifulSoup(response.text, "lxml")
            text = soup.get_text(separator=" | ")

            data = {}
            fecha = datetime.now().strftime("%Y-%m-%d")

            # Todoparacafe publica la tabla FNC con factores de rendimiento
            precio_match = re.search(
                r"Factor\s+94[^$]*\$\s*([\d.,]+)", text, re.IGNORECASE
            )
            if precio_match:
                data["precio_fnc"] = _parse_cop(precio_match.group(1))

            return CaptureResult(
                success=bool(data),
                source_id="todoparacafe",
                fecha=fecha,
                data=data,
                error=None if data else "No se encontraron datos en todoparacafe",
            )
        except Exception as e:
            return CaptureResult(
                success=False,
                source_id="todoparacafe",
                fecha=datetime.now().strftime("%Y-%m-%d"),
                error=str(e),
            )
