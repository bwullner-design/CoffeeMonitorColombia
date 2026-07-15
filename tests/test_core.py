"""
CoffeeMonitor Colombia - Tests
================================
Tests unitarios para los módulos core del sistema.
"""

import os
import sys
import unittest
from pathlib import Path
from datetime import datetime

# Setup path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Override DB path for tests
os.environ["COFFEEMONITOR_TEST"] = "1"
from config import settings
settings.DB_PATH = settings.DATA_DIR / "test_coffeemonitor.db"


class TestValidation(unittest.TestCase):
    """Tests para el motor de validación."""

    def setUp(self):
        from services.validation_service import ValidationService
        self.validator = ValidationService()

    def test_fecha_valida(self):
        result = self.validator.validate_fecha("2024-07-08")
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)

    def test_fecha_formato_invalido(self):
        result = self.validator.validate_fecha("08/07/2024")
        self.assertFalse(result.valid)

    def test_fecha_futura(self):
        result = self.validator.validate_fecha("2099-01-01")
        self.assertFalse(result.valid)

    def test_market_data_valida(self):
        data = {"precio_fnc": 2_205_000, "bolsa_ny": 292.55, "trm": 3671.75}
        result = self.validator.validate_market_data(data)
        self.assertTrue(result.valid)

    def test_market_data_fnc_fuera_rango(self):
        data = {"precio_fnc": 100}  # Muy bajo
        result = self.validator.validate_market_data(data)
        self.assertFalse(result.valid)

    def test_market_data_sin_datos(self):
        data = {}
        result = self.validator.validate_market_data(data)
        self.assertFalse(result.valid)

    def test_price_data_valida(self):
        data = {"precio_carga": 2_200_000, "factor": 94}
        result = self.validator.validate_price_data(data)
        self.assertTrue(result.valid)

    def test_price_data_sin_precio(self):
        data = {"factor": 94}
        result = self.validator.validate_price_data(data)
        self.assertFalse(result.valid)

    def test_price_data_fuera_rango(self):
        data = {"precio_carga": 50}
        result = self.validator.validate_price_data(data)
        self.assertFalse(result.valid)


class TestParseCOP(unittest.TestCase):
    """Tests para el parser de valores en COP."""

    def setUp(self):
        from scrapers.fnc_scraper import _parse_cop
        self.parse = _parse_cop

    def test_formato_puntos(self):
        self.assertEqual(self.parse("2.205.000"), 2_205_000)

    def test_formato_con_signo(self):
        self.assertEqual(self.parse("$2.205.000"), 2_205_000)

    def test_formato_comas(self):
        self.assertEqual(self.parse("2,205,000"), 2_205_000)

    def test_formato_simple(self):
        self.assertEqual(self.parse("3671.75"), 3671.75)

    def test_none(self):
        self.assertIsNone(self.parse(""))
        self.assertIsNone(self.parse(None))


class TestDatabase(unittest.TestCase):
    """Tests para la capa de base de datos."""

    @classmethod
    def setUpClass(cls):
        """Inicializar DB de prueba."""
        # Eliminar DB de test anterior si existe
        if settings.DB_PATH.exists():
            settings.DB_PATH.unlink()

        from database.schema import initialize_database, seed_sources
        initialize_database()
        seed_sources(settings.COOPERATIVAS)

    def test_market_insert_and_get(self):
        from repositories.market_repo import MarketRepository
        repo = MarketRepository()

        success = repo.insert("2024-01-15", precio_fnc=1_800_000, bolsa_ny=180.5, trm=3900.50)
        self.assertTrue(success)

        record = repo.get_by_date("2024-01-15")
        self.assertIsNotNone(record)
        self.assertEqual(record["precio_fnc"], 1_800_000)
        self.assertAlmostEqual(record["bolsa_ny"], 180.5)

    def test_market_no_duplicates(self):
        from repositories.market_repo import MarketRepository
        repo = MarketRepository()

        repo.insert("2024-01-16", precio_fnc=1_900_000)
        repo.insert("2024-01-16", precio_fnc=1_950_000)  # Duplicado, se ignora

        record = repo.get_by_date("2024-01-16")
        self.assertEqual(record["precio_fnc"], 1_900_000)  # Primer valor preservado

    def test_price_insert_and_ranking(self):
        from repositories.market_repo import MarketRepository
        from repositories.price_repo import PriceRepository

        m_repo = MarketRepository()
        p_repo = PriceRepository()

        m_repo.insert("2024-02-01", precio_fnc=2_000_000)
        p_repo.insert("2024-02-01", "coocafisa", 2_010_000)
        p_repo.insert("2024-02-01", "coop_antioquia", 2_005_000)

        ranking = p_repo.get_ranking("2024-02-01")
        self.assertEqual(len(ranking), 2)
        self.assertEqual(ranking[0]["source_id"], "coocafisa")  # Precio más alto primero

    def test_alerts_insert(self):
        from repositories.alerts_repo import AlertsRepository
        repo = AlertsRepository()

        success = repo.insert(
            fecha="2024-02-01",
            regla="R001",
            mensaje="Test alert",
            severidad="warning",
        )
        self.assertTrue(success)

        active = repo.get_active()
        self.assertTrue(len(active) > 0)

    @classmethod
    def tearDownClass(cls):
        """Limpiar DB de prueba."""
        if settings.DB_PATH.exists():
            settings.DB_PATH.unlink()


class TestRules(unittest.TestCase):
    """Tests para el motor de reglas."""

    @classmethod
    def setUpClass(cls):
        if settings.DB_PATH.exists():
            settings.DB_PATH.unlink()
        from database.schema import initialize_database, seed_sources
        initialize_database()
        seed_sources(settings.COOPERATIVAS)

    def test_r001_diferencial_alto(self):
        from repositories.market_repo import MarketRepository
        from repositories.price_repo import PriceRepository
        from repositories.alerts_repo import AlertsRepository
        from services.rules_service import RulesService

        m_repo = MarketRepository()
        p_repo = PriceRepository()
        a_repo = AlertsRepository()
        rules = RulesService()

        fecha = "2024-03-01"
        m_repo.insert(fecha, precio_fnc=2_000_000)
        p_repo.insert(fecha, "coocafisa", 2_050_000)  # Diferencial: 50.000 > 35.000

        rules.rule_r001_diferencial_max(fecha)

        alerts = a_repo.get_by_date(fecha)
        r001_alerts = [a for a in alerts if a["regla"] == "R001"]
        self.assertTrue(len(r001_alerts) > 0)

    @classmethod
    def tearDownClass(cls):
        if settings.DB_PATH.exists():
            settings.DB_PATH.unlink()


if __name__ == "__main__":
    unittest.main(verbosity=2)
