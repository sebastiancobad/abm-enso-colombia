"""Descarga todas las fuentes de datos (ONI, ERA5, SIRH, SIMMA, cuencas IDEAM).

FASE 1: esqueleto. La lógica real se implementa en Fase 2.

Uso:
    python scripts/download_all.py
    python scripts/download_all.py --solo oni,era5
"""

from __future__ import annotations

import argparse
import sys

from abm_enso.utils.paths import ensure_dirs


FUENTES_DISPONIBLES = ("oni", "era5", "sirh", "simma", "cuencas")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--solo",
        default=",".join(FUENTES_DISPONIBLES),
        help=f"Fuentes a descargar, separadas por coma. Default: todas ({FUENTES_DISPONIBLES})",
    )
    args = parser.parse_args(argv)

    ensure_dirs()
    fuentes = [f.strip().lower() for f in args.solo.split(",")]

    for fuente in fuentes:
        if fuente not in FUENTES_DISPONIBLES:
            print(f"[warn] fuente desconocida: {fuente}  — opciones: {FUENTES_DISPONIBLES}")
            continue
        print(f"[todo] descargar fuente: {fuente}  (pendiente Fase 2)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
