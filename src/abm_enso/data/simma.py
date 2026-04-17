"""Inventario SIMMA — Servicio Geológico Colombiano.

Estrategia híbrida: primero intenta descargar el CSV oficial del SGC (con
lat+lon reales), y si falla usa el CSV PDF-extract que viene versionado
en ``data/raw/Resultados_SIMMA.csv``.

IMPORTANTE: desde abril 2026, el CSV oficial del SGC es *minimalista* —
solo 13 columnas sin fecha/depto. Por eso, para la carga (`load()`) se
prioriza siempre el PDF-extract aunque el SGC esté presente.

Endpoints conocidos (abril 2026):

- ArcGIS Hub item: https://datos.sgc.gov.co/datasets/312c8792ddb24954a9d2711bd89d1afe_0
- Export CSV directo:
  https://opendata.arcgis.com/datasets/312c8792ddb24954a9d2711bd89d1afe_0.csv
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd
import requests

from abm_enso.utils import paths as _paths
from abm_enso.utils.paths import ensure_dirs

# Endpoints
HUB_CSV_URL: Final[str] = (
    "https://opendata.arcgis.com/datasets/"
    "312c8792ddb24954a9d2711bd89d1afe_0.csv"
)

HUB_GEOJSON_URL: Final[str] = (
    "https://opendata.arcgis.com/datasets/"
    "312c8792ddb24954a9d2711bd89d1afe_0.geojson"
)

# Nombres partidos típicos del PDF-extract
_NAME_FIXES: Final[dict[str, str]] = {
    "CUNDINAMA RCA": "CUNDINAMARCA",
    "MAGDALEN A":    "MAGDALENA",
}


def download(
    force: bool = False,
    out_path: Path | None = None,
    timeout: int = 180,
    verbose: bool = True,
) -> Path:
    """Descarga el CSV oficial SGC.

    Si el endpoint público falla, conserva el CSV PDF-extract ya versionado.
    El CSV del SGC no tiene fecha ni departamento (solo 13 columnas), así
    que ``load()`` prefiere el PDF-extract independientemente de cuál esté.
    """
    ensure_dirs()
    if out_path is None:
        out_path = _paths.SIMMA_CSV

    try:
        if verbose:
            print(f"[simma] intentando descarga oficial SGC: {HUB_CSV_URL}")
        resp = requests.get(HUB_CSV_URL, timeout=timeout, stream=True)
        resp.raise_for_status()

        tmp_path = out_path.with_suffix(".sgc.csv")
        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                f.write(chunk)

        if verbose:
            print(f"[simma] descarga OK: {tmp_path}")
        return tmp_path

    except requests.RequestException as e:
        if verbose:
            print(f"[simma] fallo descarga SGC ({e.__class__.__name__}); "
                  f"usando fallback local {_paths.SIMMA_CSV}")

        if not _paths.SIMMA_CSV.exists():
            raise FileNotFoundError(
                "Ni descarga SGC ni fallback local disponibles. "
                f"Falta: {_paths.SIMMA_CSV}"
            ) from e
        return _paths.SIMMA_CSV


def _leer_csv_tolerante(csv_path: Path) -> pd.DataFrame:
    """Lee CSV probando varios encodings colombianos comunes."""
    last_err = None
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            return pd.read_csv(csv_path, encoding=enc)
        except UnicodeDecodeError as e:
            last_err = e
            continue
    raise UnicodeDecodeError(
        "utf-8", b"", 0, 1,
        f"Ningún encoding funcionó para {csv_path} (último: {last_err})"
    )


def load(
    tipo: str | list[str] | None = None,
    anio_min: int | None = None,
    anio_max: int | None = None,
    auto_download: bool = True,
) -> pd.DataFrame:
    """Carga el inventario SIMMA limpio.

    Prioriza siempre el CSV PDF-extract (que tiene fecha/depto) sobre el
    CSV oficial del SGC (que solo tiene 13 columnas minimalistas).

    Args:
        tipo: ``"Deslizamiento"``, ``"Flujo"``, etc. o lista. ``None`` = todos
        anio_min, anio_max: filtro temporal (inclusivo)
        auto_download: si falta todo, intenta descargar SGC

    Returns:
        DataFrame con columnas normalizadas: ``tipo_movimiento``,
        ``fecha_evento``, ``departamento``, ``municipio``, ``longitud``, etc.
    """
    # Prioridad: PDF-extract > SGC oficial (porque el SGC no trae fecha)
    csv_path = _paths.SIMMA_CSV
    if not csv_path.exists():
        sgc_path = _paths.SIMMA_CSV.with_suffix(".sgc.csv")
        if sgc_path.exists():
            csv_path = sgc_path
        elif auto_download:
            csv_path = download()
        else:
            raise FileNotFoundError(
                f"No hay CSV SIMMA disponible. Corre `simma.download()`."
            )

    df = _leer_csv_tolerante(csv_path)
    df = _normalizar_columnas(df)
    df = _aplicar_fixes(df)

    # Filtros
    if tipo is not None and "tipo_movimiento" in df.columns:
        tipos = [tipo] if isinstance(tipo, str) else list(tipo)
        df = df[df["tipo_movimiento"].isin(tipos)]
    if anio_min is not None and "fecha_evento" in df.columns:
        df = df[df["fecha_evento"].dt.year >= anio_min]
    if anio_max is not None and "fecha_evento" in df.columns:
        df = df[df["fecha_evento"].dt.year <= anio_max]

    return df.reset_index(drop=True)


def _normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Unifica nombres entre distintas versiones del CSV (PDF-extract vs SGC).

    Estilos soportados:
    - PDF-extract: ``"Tipo movimiento"``, ``"Longitud (°)"``, etc.
    - SGC legacy: MAYÚSCULAS (``TIPO_MOV``, ``FECHA_EVENTO``)
    - SGC actual 2026: formato mixto (``Tipo_Movimiento``, ``x``, ``y``)
    """
    renames = {
        # PDF-extract style
        "Tipo movimiento":           "tipo_movimiento",
        "Fecha evento":              "fecha_evento",
        "Departamento":              "departamento",
        "Municipio":                 "municipio",
        "Vereda":                    "vereda",
        "Longitud (°)":              "longitud",
        "Latitud (°)":               "latitud",
        "Total de daños":            "total_danos",
        "Tipo movimiento (detalle)": "tipo_detalle",
        "Subtipo movimiento":        "subtipo",
        # SGC legacy UPPERCASE style
        "TIPO_MOV":      "tipo_movimiento",
        "FECHA_EVENTO":  "fecha_evento",
        "DEPARTAMENTO":  "departamento",
        "MUNICIPIO":     "municipio",
        "VEREDA":        "vereda",
        "LONGITUD":      "longitud",
        "LATITUD":       "latitud",
        "TOTAL_DANOS":   "total_danos",
        # SGC open-data 2026 (minimalista)
        "Tipo_Movimiento":    "tipo_movimiento",
        "Subtipo_Movimiento": "subtipo",
        "Subtipo_nombre":     "subtipo_detalle",
        "x":                  "longitud",
        "y":                  "latitud",
    }
    df = df.rename(columns={k: v for k, v in renames.items() if k in df.columns})
    if "fecha_evento" in df.columns:
        df["fecha_evento"] = pd.to_datetime(df["fecha_evento"], errors="coerce")
    return df


def _aplicar_fixes(df: pd.DataFrame) -> pd.DataFrame:
    """Corrige nombres partidos del PDF-extract (`CUNDINAMA RCA` → `CUNDINAMARCA`)."""
    if "departamento" in df.columns:
        df["departamento"] = df["departamento"].replace(_NAME_FIXES)
    return df
