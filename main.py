#!/usr/bin/env python3
"""
CoffeeMonitor Colombia
========================
Plataforma de inteligencia de mercado para el sector cafetero colombiano.

Uso:
    python main.py                      # Captura completa
    python main.py --init               # Inicializar base de datos
    python main.py --capture fnc        # Solo capturar FNC
    python main.py --capture trm        # Solo capturar TRM
    python main.py --capture coops      # Solo capturar cooperativas
    python main.py --import-trm 2024-01-01 2024-12-31   # Importar TRM histórica
    python main.py --export market 2024-01-01 2024-12-31  # Exportar mercado
    python main.py --export ranking 2024-07-08             # Exportar ranking
    python main.py --export alerts                         # Exportar alertas
    python main.py --status             # Mostrar estado del sistema
    python main.py --dashboard          # Mostrar dashboard en consola

Versión: 0.1.0
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import LOG_FORMAT, LOG_DATE_FORMAT, LOG_FILE, COOPERATIVAS
from database.schema import initialize_database, seed_sources
from database.connection import db


def setup_logging(verbose: bool = False):
    """Configura logging para consola y archivo."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Formato
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    
    # Consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Archivo
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def cmd_init():
    """Inicializa la base de datos y carga fuentes."""
    print("=" * 60)
    print("  CoffeeMonitor Colombia - Inicialización")
    print("=" * 60)
    initialize_database()
    seed_sources(COOPERATIVAS)
    print("\n✓ Base de datos inicializada correctamente.")
    print(f"  → {len(COOPERATIVAS)} cooperativas registradas")
    print(f"  → 3 fuentes fijas (FNC, Banco de la República, ICE)")


def cmd_capture(target: str):
    """Ejecuta captura según el objetivo."""
    from services.capture_service import capture_service

    if target == "all":
        capture_service.run_full_capture()
    elif target == "fnc":
        capture_service.capture_fnc()
    elif target == "trm":
        capture_service.capture_trm()
    elif target == "coops":
        capture_service.capture_cooperativas()
    else:
        print(f"Objetivo de captura no válido: {target}")
        print("Opciones: all, fnc, trm, coops")


def cmd_import_trm(fecha_inicio: str, fecha_fin: str):
    """Importa TRM histórica."""
    from services.capture_service import capture_service
    count = capture_service.import_trm_history(fecha_inicio, fecha_fin)
    print(f"\n✓ TRM histórica importada: {count} registros")


def cmd_export(tipo: str, args: list):
    """Exporta datos."""
    from services.export_service import export_service

    if tipo == "market" and len(args) >= 2:
        path = export_service.export_market_excel(args[0], args[1])
        print(f"\n✓ Exportación generada: {path}")
    elif tipo == "ranking":
        fecha = args[0] if args else datetime.now().strftime("%Y-%m-%d")
        path = export_service.export_ranking_excel(fecha)
        print(f"\n✓ Ranking exportado: {path}")
    elif tipo == "alerts":
        path = export_service.export_alerts_excel()
        print(f"\n✓ Alertas exportadas: {path}")
    elif tipo == "csv" and len(args) >= 2:
        path = export_service.export_market_csv(args[0], args[1])
        print(f"\n✓ CSV generado: {path}")
    else:
        print(f"Tipo de exportación no válido: {tipo}")
        print("Opciones: market <inicio> <fin>, ranking [fecha], alerts, csv <inicio> <fin>")


def cmd_status():
    """Muestra estado del sistema."""
    from repositories.market_repo import market_repo
    from repositories.alerts_repo import alerts_repo
    from repositories.sources_repo import sources_repo

    print("\n" + "=" * 60)
    print("  CoffeeMonitor Colombia - Estado del Sistema")
    print("=" * 60)

    # Último dato de mercado
    latest = market_repo.get_latest()
    if latest:
        print(f"\n  Último dato de mercado:")
        print(f"    Fecha:      {latest['fecha']}")
        if latest.get('precio_fnc'):
            print(f"    Precio FNC: ${latest['precio_fnc']:,.0f} COP/carga")
        if latest.get('bolsa_ny'):
            print(f"    Bolsa NY:   {latest['bolsa_ny']:.2f} ¢/lb")
        if latest.get('trm'):
            print(f"    TRM:        ${latest['trm']:,.2f} COP/USD")
    else:
        print("\n  ⚠ No hay datos de mercado.")

    # Total de registros
    total = market_repo.count()
    print(f"\n  Registros de mercado: {total}")

    # Alertas activas
    active_alerts = alerts_repo.count_active()
    print(f"  Alertas activas:      {active_alerts}")

    # Fuentes
    sources = sources_repo.get_all_active()
    print(f"  Fuentes activas:      {len(sources)}")
    for s in sources:
        print(f"    → [{s['tipo']:12s}] {s['nombre']}")

    print()


def cmd_dashboard():
    """Dashboard de consola."""
    from repositories.market_repo import market_repo
    from repositories.price_repo import price_repo
    from repositories.alerts_repo import alerts_repo

    today = datetime.now().strftime("%Y-%m-%d")

    print("\n" + "═" * 70)
    print("  ☕  CoffeeMonitor Colombia  ☕")
    print(f"  {datetime.now().strftime('%A %d de %B de %Y, %H:%M')}")
    print("═" * 70)

    # Mercado
    latest = market_repo.get_latest()
    if latest:
        print(f"\n  ┌─────────────────────────────────────────────────────┐")
        print(f"  │  MERCADO  ({latest['fecha']})                       │")
        print(f"  ├─────────────────────────────────────────────────────┤")
        if latest.get('precio_fnc'):
            print(f"  │  Precio FNC:   ${latest['precio_fnc']:>12,.0f} COP/carga  │")
        if latest.get('bolsa_ny'):
            print(f"  │  Bolsa NY:     {latest['bolsa_ny']:>12.2f} ¢/lb         │")
        if latest.get('trm'):
            print(f"  │  TRM:          ${latest['trm']:>12,.2f} COP/USD      │")
        print(f"  └─────────────────────────────────────────────────────┘")

        # Variación vs día anterior
        prev = market_repo.get_previous(latest['fecha'])
        if prev and prev.get('precio_fnc') and latest.get('precio_fnc'):
            var = latest['precio_fnc'] - prev['precio_fnc']
            var_pct = (var / prev['precio_fnc']) * 100
            arrow = "▲" if var > 0 else "▼" if var < 0 else "─"
            print(f"  {arrow} Var. diaria: ${var:+,.0f} ({var_pct:+.1f}%)")

    # Ranking cooperativas
    ranking = price_repo.get_ranking(today)
    if ranking:
        print(f"\n  ┌─────────────────────────────────────────────────────┐")
        print(f"  │  RANKING COOPERATIVAS ({today})                     │")
        print(f"  ├─────────────────────────────────────────────────────┤")
        for i, r in enumerate(ranking[:10], 1):
            nombre = r['cooperativa'][:30]
            dif = r.get('diferencial')
            dif_str = f"({dif:+,.0f})" if dif is not None else ""
            print(f"  │  {i:2d}. {nombre:<30s} ${r['precio_carga']:>10,.0f} {dif_str}")
        print(f"  └─────────────────────────────────────────────────────┘")

    # Alertas
    alerts = alerts_repo.get_active(limit=5)
    if alerts:
        icons = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
        print(f"\n  ALERTAS ACTIVAS ({alerts_repo.count_active()} total)")
        print(f"  {'─' * 60}")
        for a in alerts:
            icon = icons.get(a['severidad'], '⚪')
            print(f"  {icon} [{a['regla']}] {a['mensaje'][:55]}")

    print(f"\n{'═' * 70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="CoffeeMonitor Colombia - Inteligencia de Mercado Cafetero",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--init", action="store_true", help="Inicializar base de datos")
    parser.add_argument("--capture", nargs="?", const="all",
                        help="Capturar datos (all|fnc|trm|coops)")
    parser.add_argument("--import-trm", nargs=2, metavar=("INICIO", "FIN"),
                        help="Importar TRM histórica")
    parser.add_argument("--export", nargs="+",
                        help="Exportar (market|ranking|alerts|csv) [args]")
    parser.add_argument("--status", action="store_true", help="Estado del sistema")
    parser.add_argument("--dashboard", action="store_true", help="Dashboard en consola")
    parser.add_argument("-v", "--verbose", action="store_true", help="Modo verbose")

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Si no hay argumentos, mostrar ayuda
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # Inicializar DB siempre
    initialize_database()
    seed_sources(COOPERATIVAS)

    if args.init:
        cmd_init()
    elif args.capture:
        cmd_capture(args.capture)
    elif args.import_trm:
        cmd_import_trm(args.import_trm[0], args.import_trm[1])
    elif args.export:
        cmd_export(args.export[0], args.export[1:])
    elif args.status:
        cmd_status()
    elif args.dashboard:
        cmd_dashboard()


if __name__ == "__main__":
    main()
