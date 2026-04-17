"""Orquestador de descarga — importable por el CLI y el script.

Concentra la lógica que antes vivía solo en ``scripts/download_all.py``
para poder llamarla tanto desde CLI (``abm-enso download``) como desde
un ``python scripts/download_all.py`` directo.
"""

from __future__ import annotations

import time
import traceback
from typing import Iterable

from abm_enso.data import cuencas, era5, oni, simma, sirh
from abm_enso.utils.paths import ensure_dirs

FUENTES_DISPONIBLES = ("oni", "era5", "sirh", "simma", "cuencas")


def descargar_todas(
    solo: Iterable[str] = FUENTES_DISPONIBLES,
    force: bool = False,
    era5_mode: str = "daily",
    skip_on_error: bool = False,
) -> dict[str, tuple[bool, str]]:
    """Descarga las fuentes indicadas y retorna el resumen.

    Args:
        solo: fuentes a descargar (subset de FUENTES_DISPONIBLES)
        force: re-descargar aunque exista cache
        era5_mode: ``"daily"`` o ``"monthly"``
        skip_on_error: continuar con las siguientes si una falla

    Returns:
        dict ``{fuente: (ok: bool, info: str)}``
    """
    ensure_dirs()
    results: dict[str, tuple[bool, str]] = {}

    for fuente in solo:
        if fuente not in FUENTES_DISPONIBLES:
            results[fuente] = (False, "desconocida")
            continue

        print(f"\n{'='*60}\n→ {fuente.upper()}\n{'='*60}")
        t0 = time.perf_counter()
        try:
            if fuente == "oni":
                oni.download(force=force)
            elif fuente == "era5":
                era5.download(mode=era5_mode, force=force)
            elif fuente == "sirh":
                sirh.download(force=force)
            elif fuente == "simma":
                simma.download(force=force)
            elif fuente == "cuencas":
                cuencas.download(force=force)
            dt = time.perf_counter() - t0
            results[fuente] = (True, f"{dt:.1f}s")
            print(f"[ok] {fuente} completo en {dt:.1f}s")
        except Exception as e:
            dt = time.perf_counter() - t0
            results[fuente] = (False, f"{e.__class__.__name__}: {e}")
            print(f"[FAIL] {fuente} en {dt:.1f}s — {e}")
            traceback.print_exc()
            if not skip_on_error:
                break

    _imprimir_resumen(results)
    return results


def _imprimir_resumen(results: dict[str, tuple[bool, str]]) -> None:
    print(f"\n{'='*60}\nRESUMEN\n{'='*60}")
    for fuente, (ok, info) in results.items():
        status = "✓" if ok else "✗"
        print(f"  {status}  {fuente:10s} {info}")
