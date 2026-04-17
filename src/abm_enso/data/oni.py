"""Índice Oceánico Niño (ONI) de NOAA/CPC.

Refactor de `Fuente_1.py` con:
- caché local para evitar re-descargas
- parser robusto (NOAA cambia ocasionalmente el layout)
- API funcional simple: ``load()``, ``download()``, ``plot()``

Ejemplo:
    >>> from abm_enso.data import oni
    >>> df = oni.load()
    >>> df.head()
                oni
    fecha
    1950-01-01 -1.53
    1950-02-01 -1.34
    ...

Fuente oficial:
    https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Final

import pandas as pd
import requests

from abm_enso.utils import paths as _paths
from abm_enso.utils.paths import ensure_dirs

ONI_URL: Final[str] = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
"""URL del archivo plano delimitado por espacios publicado por NOAA/CPC."""

# Mapeo de trimestres rolling a mes central
_SEAS_TO_MONTH: Final[dict[str, int]] = {
    "DJF": 1,  "JFM": 2,  "FMA": 3,  "MAM": 4,
    "AMJ": 5,  "MJJ": 6,  "JJA": 7,  "JAS": 8,
    "ASO": 9,  "SON": 10, "OND": 11, "NDJ": 12,
}


def download(
    force: bool = False,
    out_path: Path | None = None,
    timeout: int = 60,
) -> Path:
    """Descarga el archivo plano ONI y lo guarda como CSV limpio."""
    ensure_dirs()
    if out_path is None:
        out_path = _paths.ONI_CSV
    if out_path.exists() and not force:
        return out_path

    resp = requests.get(ONI_URL, timeout=timeout)
    resp.raise_for_status()

    df = _parse_noaa_ascii(resp.text)
    df.to_csv(out_path)
    return out_path


def load(
    start: str | None = None,
    end: str | None = None,
    auto_download: bool = True,
) -> pd.DataFrame:
    """Carga la serie ONI mensual como DataFrame indexado por fecha."""
    if not _paths.ONI_CSV.exists():
        if auto_download:
            download()
        else:
            raise FileNotFoundError(
                f"{_paths.ONI_CSV} no existe. Corre `abm_enso.data.oni.download()` primero."
            )

    df = pd.read_csv(_paths.ONI_CSV, index_col="fecha", parse_dates=["fecha"])
    if start is not None:
        df = df.loc[start:]
    if end is not None:
        df = df.loc[:end]
    return df


def _parse_noaa_ascii(text: str) -> pd.DataFrame:
    """Parser del archivo plano NOAA/CPC ``oni.ascii.txt``.

    El formato real tiene 4 columnas separadas por espacios:

        SEAS  YR  TOTAL  ANOM
        DJF  1950  26.16  -1.53
        JFM  1950  26.30  -1.34
        ...

    Detectamos automáticamente cuál columna es la anomalía para ser robustos
    a cambios de orden o renombramientos menores.
    """
    df = pd.read_csv(io.StringIO(text), sep=r"\s+", engine="python")
    cols = df.columns.tolist()

    # Columna de temporada (strings tipo "DJF")
    col_seas = cols[0]

    # Columna del año (toda ella en rango razonable 1900-2030)
    col_yr = next(c for c in cols[1:] if df[c].between(1900, 2030).all())

    # Columna de anomalía: la única numérica con |valores| < 10
    col_anom = next(
        c for c in cols
        if c not in (col_seas, col_yr)
        and pd.api.types.is_numeric_dtype(df[c])
        and df[c].abs().max() < 10
    )

    df["month"] = df[col_seas].str.strip().map(_SEAS_TO_MONTH)
    df = df[df["month"].notna()].copy()
    df["fecha"] = pd.to_datetime({
        "year":  df[col_yr].astype(int),
        "month": df["month"].astype(int),
        "day":   1,
    })

    out = df.set_index("fecha")[[col_anom]].rename(columns={col_anom: "oni"})
    return out.sort_index()
