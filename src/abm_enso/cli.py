"""Entry point de línea de comandos para el pipeline ABM-ENSO-Colombia.

Uso:
    abm-enso download              # descarga todas las fuentes
    abm-enso calibrate             # recalibra β₁, θ, κ contra SIMMA
    abm-enso simulate --scenario nina-2010
    abm-enso viz                   # abre la app Solara

Los subcomandos se implementan en las Fases 2-5. En Fase 1 el CLI existe
solo como esqueleto para que `pip install -e .` registre el entry point.
"""

from __future__ import annotations

import argparse
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="abm-enso",
        description="Pipeline ABM-ENSO-Colombia — Modelo 1 (Clima/Cuencas)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("download", help="Descargar todas las fuentes de datos")
    sub.add_parser("calibrate", help="Recalibrar β₁, θ, κ contra SIMMA")

    p_sim = sub.add_parser("simulate", help="Correr el ABM de cuencas")
    p_sim.add_argument(
        "--scenario",
        default="nina-2010",
        choices=["nina-2010", "nino-2015", "neutro", "custom"],
    )
    p_sim.add_argument("--meses", type=int, default=60)
    p_sim.add_argument("--replicas", type=int, default=30)

    sub.add_parser("viz", help="Abrir la app Solara (tipo NetLogo)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # TODO (Fases 2-5): despachar a los módulos correspondientes
    print(f"[abm-enso] comando reconocido: {args.command}")
    print("[abm-enso] implementación pendiente — ver roadmap en README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
