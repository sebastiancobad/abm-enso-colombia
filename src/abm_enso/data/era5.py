"""ERA5-Land desde Copernicus Climate Data Store.

Descarga y procesa tres variables clave para el ABM de cuencas:

- ``tp``    (total_precipitation)          → precipitación [mm/mes]
- ``ro``    (runoff)                       → escorrentía [mm/mes]
- ``swvl1`` (volumetric_soil_water_layer_1) → humedad del suelo [% vol.]

Modo de descarga: ``daily`` agregado a mensual (~150 MB, ~30 min).
Esto nos deja la puerta abierta para resolución diaria en el futuro sin
re-descargar, y al mismo tiempo produce los mensuales para el ABM.

Requiere:
    - Cuenta gratuita en https://cds.climate.copernicus.eu
    - Archivo ``~/.cdsapirc`` configurado
    - Aceptación manual de los términos del dataset ERA5-Land

Ver ``docs/instalacion.md`` para los pasos detallados.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    import xarray as xr

from abm_enso.utils.constants import COLOMBIA_AREA_ERA5, YEAR_END, YEAR_START
from abm_enso.utils import paths as _paths
from abm_enso.utils.paths import ensure_dirs

# ==========================================================
# Configuración del dataset
# ==========================================================
DATASET_MONTHLY: str = "reanalysis-era5-land-monthly-means"
DATASET_DAILY: str = "reanalysis-era5-land"

# Variables y su modo de conversión a unidades físicas
_VARIABLES_FLUJO = ("total_precipitation", "runoff")  # m → mm
_VARIABLES_ESTADO = ("volumetric_soil_water_layer_1",)  # frac → % vol

VARIABLE_ABREV = {
    "total_precipitation":           "tp",
    "runoff":                        "ro",
    "volumetric_soil_water_layer_1": "swvl1",
}


# ==========================================================
# Descarga
# ==========================================================
def download(
    mode: Literal["monthly", "daily"] = "daily",
    year_start: int = YEAR_START,
    year_end: int = YEAR_END,
    force: bool = False,
    chunk_years: int = 5,
) -> tuple[Path, Path]:
    """Descarga ERA5-Land desde Copernicus CDS en chunks para evitar el límite de costo.

    Args:
        mode: ``"monthly"`` es rápido (~15 MB), ``"daily"`` permite
              re-agregar a distintas resoluciones (~150 MB, ~30 min).
        year_start, year_end: rango inclusivo
        force: re-descargar aunque los archivos existan
        chunk_years: años por request (5 años daily ≈ 30 MB, seguro bajo el límite).
                     Si Copernicus rechaza con "cost limits exceeded", baja este número.

    Returns:
        (path_flujos, path_estado) — dos NetCDF concatenados.

    Nota sobre el stepType:
        Copernicus entrega dos NetCDF distintos cuando se piden variables
        con ``stepType`` diferente:
          - ``avgad``: acumulaciones promediadas (tp, ro)
          - ``avgua``: estado instantáneo promediado (swvl1)

    Nota sobre el chunking:
        El modo daily con rango completo 1981-2024 excede el límite de costo
        de Copernicus (~50k elementos por request). Lo dividimos en bloques
        de ``chunk_years`` años y concatenamos al final con xarray.
    """
    ensure_dirs()

    if _paths.ERA5_NC_FLUJOS.exists() and _paths.ERA5_NC_ESTADO.exists() and not force:
        return _paths.ERA5_NC_FLUJOS, _paths.ERA5_NC_ESTADO

    # Import perezoso: cdsapi solo si realmente se descarga
    import cdsapi
    import xarray as xr

    client = cdsapi.Client()

    dataset = DATASET_MONTHLY if mode == "monthly" else DATASET_DAILY
    tmp_dir = _paths.DATA_RAW / "_era5_chunks"
    tmp_dir.mkdir(exist_ok=True)

    chunks_flujos: list[Path] = []
    chunks_estado: list[Path] = []

    # Iterar en bloques de chunk_years años
    for y0 in range(year_start, year_end + 1, chunk_years):
        y1 = min(y0 + chunk_years - 1, year_end)
        print(f"[era5] bloque {y0}-{y1}...")

        base_request = {
            "product_type": "monthly_averaged_reanalysis" if mode == "monthly" else "reanalysis",
            "year":         [str(y) for y in range(y0, y1 + 1)],
            "month":        [f"{m:02d}" for m in range(1, 13)],
            "time":         "00:00",
            "data_format":  "netcdf",
            "area":         COLOMBIA_AREA_ERA5,
        }
        if mode == "daily":
            base_request["day"] = [f"{d:02d}" for d in range(1, 32)]

        # Chunk de flujos
        out_f = tmp_dir / f"flujos_{y0}_{y1}.nc"
        if not out_f.exists() or force:
            req_flujos = {**base_request, "variable": list(_VARIABLES_FLUJO)}
            client.retrieve(dataset, req_flujos, str(out_f))
        chunks_flujos.append(out_f)

        # Chunk de estado
        out_e = tmp_dir / f"estado_{y0}_{y1}.nc"
        if not out_e.exists() or force:
            req_estado = {**base_request, "variable": list(_VARIABLES_ESTADO)}
            client.retrieve(dataset, req_estado, str(out_e))
        chunks_estado.append(out_e)

    # Concatenar los chunks con xarray y guardar los NetCDF finales
    print("[era5] concatenando chunks...")
    _concatenar_nc(chunks_flujos, _paths.ERA5_NC_FLUJOS)
    _concatenar_nc(chunks_estado, _paths.ERA5_NC_ESTADO)

    return _paths.ERA5_NC_FLUJOS, _paths.ERA5_NC_ESTADO


def _concatenar_nc(chunks: list[Path], out_path: Path) -> None:
    """Concatena NetCDFs temporales a lo largo del eje temporal y guarda el resultado."""
    import xarray as xr

    time_dim = None
    datasets = []
    for chunk_path in sorted(chunks):
        ds = xr.open_dataset(chunk_path)
        if time_dim is None:
            time_dim = "valid_time" if "valid_time" in ds.coords else "time"
        datasets.append(ds)

    merged = xr.concat(datasets, dim=time_dim)
    merged = merged.sortby(time_dim)
    merged.to_netcdf(out_path)
    for ds in datasets:
        ds.close()


# ==========================================================
# Carga y procesamiento
# ==========================================================
def load(
    variable: Literal["tp", "ro", "swvl1"] | None = None,
    auto_download: bool = True,
) -> pd.DataFrame:
    """Carga ERA5 consolidado por mes (promedio espacial sobre Colombia).

    Si no existe el consolidado pero sí los NetCDF crudos, lo genera al vuelo.

    Args:
        variable: si se especifica, devuelve solo esa columna + ``fecha``;
                  si es ``None``, devuelve el consolidado completo con las 3
        auto_download: si faltan los NetCDF y ``True``, intenta descargarlos

    Returns:
        DataFrame indexado por ``fecha`` con columnas (según ``variable``):
        ``precip_mm_mes``, ``runoff_mm_mes``, ``humedad_suelo_pct``.
    """
    if not _paths.ERA5_CONSOLIDADO.exists():
        if _paths.ERA5_NC_FLUJOS.exists() and _paths.ERA5_NC_ESTADO.exists():
            build_consolidado()
        elif auto_download:
            download()
            build_consolidado()
        else:
            raise FileNotFoundError(
                f"{_paths.ERA5_CONSOLIDADO} no existe. Corre `era5.download()` primero."
            )

    df = pd.read_csv(_paths.ERA5_CONSOLIDADO, parse_dates=["fecha"]).set_index("fecha")

    if variable is None:
        return df

    col_map = {
        "tp":    "precip_mm_mes",
        "ro":    "runoff_mm_mes",
        "swvl1": "humedad_suelo_pct",
    }
    return df[[col_map[variable]]]


def build_consolidado(
    nc_flujos: Path | None = None,
    nc_estado: Path | None = None,
    out_csv: Path | None = None,
) -> Path:
    """Construye el CSV consolidado mensual a partir de los dos NetCDF.

    Si los NetCDF son daily, primero se agregan a mensual:
        - tp, ro: SUMA diaria * 1000 (m→mm)
        - swvl1: PROMEDIO diario * 100 (frac→%)

    Si los NetCDF son monthly-means, se aplica la fórmula del ``Fuente_2.py``:
        - tp, ro: valor * 1000 * días_del_mes
        - swvl1: valor * 100
    """
    ensure_dirs()
    if nc_flujos is None:
        nc_flujos = _paths.ERA5_NC_FLUJOS
    if nc_estado is None:
        nc_estado = _paths.ERA5_NC_ESTADO
    if out_csv is None:
        out_csv = _paths.ERA5_CONSOLIDADO

    df_tp = _cargar_variable(nc_flujos, "tp", conversion="flujo")
    df_ro = _cargar_variable(nc_flujos, "ro", conversion="flujo")
    df_sm = _cargar_variable(nc_estado, "swvl1", conversion="estado")

    out = (
        df_tp[["fecha", "valor"]].rename(columns={"valor": "precip_mm_mes"})
        .merge(
            df_ro[["fecha", "valor"]].rename(columns={"valor": "runoff_mm_mes"}),
            on="fecha",
        )
        .merge(
            df_sm[["fecha", "valor"]].rename(columns={"valor": "humedad_suelo_pct"}),
            on="fecha",
        )
    )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)
    return out_csv


def _cargar_variable(
    nc_path: Path,
    var_name: str,
    conversion: Literal["flujo", "estado"],
) -> pd.DataFrame:
    """Carga una variable del NetCDF, promedia espacialmente, agrega y convierte."""
    import xarray as xr

    ds = xr.open_dataset(nc_path)

    # Copernicus cambió `time` → `valid_time` en 2024
    time_coord = "valid_time" if "valid_time" in ds.coords else "time"

    serie = ds[var_name].mean(dim=["latitude", "longitude"])
    df = serie.to_dataframe().reset_index().rename(columns={time_coord: "fecha"})
    df = df[["fecha", var_name]].copy()

    # Detectar si ya es mensual o viene daily
    freq_inferida = pd.infer_freq(df["fecha"][:10])
    es_daily = freq_inferida in ("D", "H", None) and len(df) > 12 * 50  # heurística

    if es_daily:
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.to_period("M").dt.to_timestamp()
        if conversion == "flujo":
            # Sumar diarios -> mensual; m -> mm
            df = df.groupby("fecha", as_index=False)[var_name].sum()
            df["valor"] = df[var_name] * 1000
        else:  # estado
            df = df.groupby("fecha", as_index=False)[var_name].mean()
            df["valor"] = df[var_name] * 100
    else:  # ya es monthly
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.to_period("M").dt.to_timestamp()
        if conversion == "flujo":
            df["valor"] = df[var_name] * 1000 * df["fecha"].dt.days_in_month
        else:
            df["valor"] = df[var_name] * 100

    return df.dropna(subset=["valor"]).reset_index(drop=True)
