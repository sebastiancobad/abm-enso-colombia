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

    p_dl = sub.add_parser("download", help="Descargar todas las fuentes de datos")
    p_dl.add_argument("--solo", default="oni,era5,sirh,simma,cuencas")
    p_dl.add_argument("--force", action="store_true")
    p_dl.add_argument("--era5-mode", choices=["daily", "monthly"], default="daily")
    p_dl.add_argument("--era5-chunk-years", type=int, default=5,
                      help="Años por request ERA5 (default 5, baja a 2-3 si cost limit)")
    p_dl.add_argument("--skip-on-error", action="store_true")

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

    if args.command == "download":
        from abm_enso.pipeline import descargar_todas

        fuentes = [f.strip().lower() for f in args.solo.split(",")]
        results = descargar_todas(
            solo=fuentes,
            force=args.force,
            era5_mode=args.era5_mode,
            era5_chunk_years=args.era5_chunk_years,
            skip_on_error=args.skip_on_error,
        )
        return 0 if all(ok for ok, _ in results.values()) else 1

    if args.command == "calibrate":
        from abm_enso.pipeline import calibrar_modelo
        calibrar_modelo()
        return 0

    # TODO (Fases 4-5): despachar a los módulos correspondientes
    print(f"[abm-enso] comando reconocido: {args.command}")
    print("[abm-enso] implementación pendiente — ver roadmap en README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
