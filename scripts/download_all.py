"""Entry point CLI para descargar todas las fuentes de datos.

Uso:
    python scripts/download_all.py
    python scripts/download_all.py --solo oni,simma
    python scripts/download_all.py --force --era5-mode monthly
    python scripts/download_all.py --skip-on-error

La lógica real vive en ``abm_enso.pipeline.descargar_todas`` para ser
reutilizable desde el CLI ``abm-enso download``.
"""

from __future__ import annotations

import argparse
import sys

from abm_enso.pipeline import FUENTES_DISPONIBLES, descargar_todas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo", default=",".join(FUENTES_DISPONIBLES))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--era5-mode", choices=["daily", "monthly"], default="daily")
    parser.add_argument("--skip-on-error", action="store_true")
    args = parser.parse_args(argv)

    fuentes = [f.strip().lower() for f in args.solo.split(",")]
    results = descargar_todas(
        solo=fuentes,
        force=args.force,
        era5_mode=args.era5_mode,
        skip_on_error=args.skip_on_error,
    )
    return 0 if all(ok for ok, _ in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
