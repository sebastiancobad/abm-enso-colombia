"""Inventario SIMMA — Servicio Geológico Colombiano.

Estrategia híbrida: primero intenta descargar el CSV oficial del SGC (con
lat+lon reales), y si falla usa el CSV PDF-extract que viene versionado
en ``data/raw/Resultados_SIMMA.csv``.

Endpoints conocidos (abril 2026):

- ArcGIS Hub item: https://datos.sgc.gov.co/datasets/312c8792ddb24954a9d2711bd89d1afe_0
- Export CSV directo (si disponible):
  https://opendata.arcgis.com/datasets/312c8792ddb24954a9d2711bd89d1afe_0.csv
- FeatureServer REST (siempre funciona si el anterior 404):
  https://srvags.sgc.gov.co/arcgis/rest/services/.../FeatureServer/0/query
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd
import requests

from abm_enso.utils import paths as _paths
from abm_enso.utils.paths import ensure_dirs

# Endpoints (orden de prioridad)
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
    """Descarga el CSV oficial SGC con lat+lon reales.

    Si el endpoint público falla, conserva el CSV PDF-extract ya versionado
    y lo renombra explícitamente para que el usuario sepa cuál tiene.

    Args:
        force: re-descargar aunque exista un CSV SGC oficial previo
        out_path: ruta final. Si es ``None``, usa ``paths.SIMMA_CSV``
        timeout: segundos antes de abortar

    Returns:
        Path del CSV disponible (oficial si descarga OK, PDF-extract si no).
    """
    ensure_dirs()
    if out_path is None:
        out_path = _paths.SIMMA_CSV

    # Intento 1: export CSV directo del ArcGIS Hub
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


def load(
    tipo: str | list[str] | None = None,
    anio_min: int | None = None,
    anio_max: int | None = None,
    auto_download: bool = True,
) -> pd.DataFrame:
    """Carga el inventario SIMMA limpio.

    Args:
        tipo: ``"Deslizamiento"``, ``"Flujo"``, etc. o lista. ``None`` = todos
        anio_min, anio_max: filtro temporal (inclusivo)
        auto_download: si falta, intenta descargar SGC, cae al CSV local

    Returns:
        DataFrame con columnas: ``tipo_movimiento``, ``fecha_evento``,
        ``departamento``, ``municipio``, ``vereda``, ``longitud``,
        ``latitud`` (si disponible), ``total_danos``.
    """
    # El CSV PDF-extract tiene fecha/depto; el SGC oficial es minimalista.
    # Por eso priorizamos el PDF-extract siempre que exista.
    csv_path = _paths.SIMMA_CSV
    if not csv_path.exists():
        sgc_path = _paths.SIMMA_CSV.with_suffix(".sgc.csv")
        if sgc_path.exists():
            csv_path = sgc_path

    if not csv_path.exists():
        if auto_download:
            csv_path = download()
        else:
            raise FileNotFoundError(
                f"No hay CSV SIMMA disponible (ni {sgc_path} ni {_paths.SIMMA_CSV}). "
                "Corre `simma.download()`."
            )

    # Lectura tolerante a distintos encodings colombianos (utf-8-sig, utf-8, latin-1, cp1252)
    df = None
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(csv_path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        raise UnicodeDecodeError("utf-8", b"", 0, 1, f"Ningún encoding funcionó para {csv_path}")
    df = _normalizar_columnas(df)
    df = _aplicar_fixes(df)

    # Filtros
    if tipo is not None:
        tipos = [tipo] if isinstance(tipo, str) else list(tipo)
        df = df[df["tipo_movimiento"].isin(tipos)]
    if anio_min is not None:
        df = df[df["fecha_evento"].dt.year >= anio_min]
    if anio_max is not None:
        df = df[df["fecha_evento"].dt.year <= anio_max]

    return df.reset_index(drop=True)


def _normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Unifica nombres entre el CSV PDF-extract y el CSV oficial del SGC.

    Los headers oficiales del SGC están en MAYÚSCULAS_SIN_TILDES
    (ej. ``TIPO_MOV``, ``FECHA_EVENTO``, ``LATITUD``, ``LONGITUD``).
    El PDF-extract tiene espacios y acentos (ej. ``Tipo movimiento``,
    ``Longitud (°)``).
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
        # SGC official style
        "TIPO_MOV":      "tipo_movimiento",
        "FECHA_EVENTO":  "fecha_evento",
        "DEPARTAMENTO":  "departamento",
        "MUNICIPIO":     "municipio",
        "VEREDA":        "vereda",
        "LONGITUD":      "longitud",
        "LATITUD":       "latitud",
        "TOTAL_DANOS":   "total_danos",
        # SGC open-data (ArcGIS Hub) style
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
