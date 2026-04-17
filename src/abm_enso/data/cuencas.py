"""Zonificación hidrográfica IDEAM — estrategia de descarga 3-tier.

El shapefile oficial cambia de ubicación a menudo. Probamos en orden:

1. **ArcGIS Hub** (IDEAM + SiGaia) — export GeoJSON directo, sin login
2. **SIAC / IDEAM** — descarga manual por visor, evitamos y saltamos
3. **HydroBASINS nivel 6** — fallback global, garantizado

El resultado se convierte siempre al mismo esquema: un GeoPackage con
columnas ``id_cuenca``, ``nombre``, ``area_hidrografica``, ``geometry``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import requests

from abm_enso.utils.constants import COLOMBIA_BBOX
from abm_enso.utils import paths as _paths
from abm_enso.utils.paths import ensure_dirs

# ==========================================================
# Endpoints conocidos (probados Apr 2026)
# ==========================================================
ARCGIS_HUB_IDEAM_ITEM_ID: Final[str] = "89f6818e093f4b0faa99b456ad98018d"

ARCGIS_HUB_GEOJSON_URL: Final[str] = (
    f"https://opendata.arcgis.com/datasets/{ARCGIS_HUB_IDEAM_ITEM_ID}.geojson"
)

# HydroBASINS fallback — nivel 6 (~8000 cuencas globales, ~316 en Colombia)
# El archivo oficial es un shapefile en zip. HydroSHEDS lo sirve desde un bucket.
HYDROBASINS_SA_URL: Final[str] = (
    "https://data.hydrosheds.org/file/HydroBASINS/standard/"
    "hybas_sa_lev06_v1c.zip"
)


def download(
    force: bool = False,
    out_path: Path | None = None,
    timeout: int = 180,
    verbose: bool = True,
) -> Path:
    """Descarga cuencas con fallback 3-tier. Guarda como GeoPackage unificado.

    Args:
        force: re-descargar aunque ya exista el GPKG local
        out_path: ruta del GeoPackage final. ``None`` usa ``paths.CUENCAS_GPKG``
        timeout: segundos antes de abortar cada intento
        verbose: imprimir qué endpoint se está intentando

    Returns:
        Path al GeoPackage generado.

    Raises:
        RuntimeError: si todos los endpoints fallan
    """
    ensure_dirs()
    if out_path is None:
        out_path = _paths.CUENCAS_GPKG

    if out_path.exists() and not force:
        if verbose:
            print(f"[cuencas] cache hit: {out_path}")
        return out_path

    # Tier 1: ArcGIS Hub (IDEAM oficial)
    try:
        if verbose:
            print("[cuencas] tier 1: ArcGIS Hub IDEAM...")
        return _download_arcgis_hub(out_path, timeout, verbose)
    except Exception as e:
        if verbose:
            print(f"[cuencas] tier 1 fallo: {e.__class__.__name__}: {e}")

    # Tier 2: HydroBASINS (fallback garantizado)
    try:
        if verbose:
            print("[cuencas] tier 2: HydroBASINS nivel 6...")
        return _download_hydrobasins(out_path, timeout, verbose)
    except Exception as e:
        if verbose:
            print(f"[cuencas] tier 2 fallo: {e.__class__.__name__}: {e}")

    raise RuntimeError(
        "Todos los endpoints de cuencas fallaron. "
        "Descarga manual: http://www.siac.gov.co/catalogo-de-mapas"
    )


def load(auto_download: bool = True):
    """Carga el GeoDataFrame de cuencas con esquema unificado.

    Returns:
        GeoDataFrame con columnas:
            - ``id_cuenca`` (str) — identificador único
            - ``nombre`` (str)
            - ``area_hidrografica`` (str) — clasificación gruesa
            - ``geometry`` (polygon, CRS EPSG:4326)
    """
    import geopandas as gpd

    if not _paths.CUENCAS_GPKG.exists():
        if auto_download:
            download()
        else:
            raise FileNotFoundError(
                f"{_paths.CUENCAS_GPKG} no existe. Corre `cuencas.download()`."
            )

    return gpd.read_file(_paths.CUENCAS_GPKG)


# ==========================================================
# Implementaciones por tier
# ==========================================================
def _download_arcgis_hub(
    out_path: Path,
    timeout: int,
    verbose: bool,
) -> Path:
    """Descarga desde ArcGIS Hub como GeoJSON y convierte a GPKG."""
    import geopandas as gpd

    resp = requests.get(ARCGIS_HUB_GEOJSON_URL, timeout=timeout)
    resp.raise_for_status()

    tmp_geojson = out_path.with_suffix(".hub.geojson")
    tmp_geojson.write_bytes(resp.content)

    gdf = gpd.read_file(tmp_geojson)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        gdf = gdf.to_crs(epsg=4326)

    gdf = _clip_colombia(gdf)
    gdf = _unificar_esquema(gdf, source="arcgis_hub")
    gdf.to_file(out_path, driver="GPKG", layer="cuencas")

    if verbose:
        print(f"[cuencas] OK ArcGIS Hub: {len(gdf)} polígonos → {out_path}")
    return out_path


def _download_hydrobasins(
    out_path: Path,
    timeout: int,
    verbose: bool,
) -> Path:
    """Descarga HydroBASINS Sudamérica nivel 6 y filtra por bbox Colombia."""
    import io
    import zipfile

    import geopandas as gpd

    resp = requests.get(HYDROBASINS_SA_URL, timeout=timeout, stream=True)
    resp.raise_for_status()

    # Extraer el shapefile del zip en un tmp
    tmp_dir = out_path.parent / "_hydrobasins_tmp"
    tmp_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        zf.extractall(tmp_dir)

    shp_path = next(tmp_dir.rglob("*.shp"))
    gdf = gpd.read_file(shp_path).to_crs(epsg=4326)

    gdf = _clip_colombia(gdf)
    gdf = _unificar_esquema(gdf, source="hydrobasins")
    gdf.to_file(out_path, driver="GPKG", layer="cuencas")

    # Cleanup
    for f in tmp_dir.rglob("*"):
        f.unlink()
    tmp_dir.rmdir()

    if verbose:
        print(f"[cuencas] OK HydroBASINS: {len(gdf)} polígonos → {out_path}")
    return out_path


def _clip_colombia(gdf):
    """Filtra polígonos que intersectan el bbox de Colombia."""
    lon_min, lat_min, lon_max, lat_max = COLOMBIA_BBOX
    return gdf.cx[lon_min:lon_max, lat_min:lat_max].copy()


def _unificar_esquema(gdf, source: str):
    """Homogeniza columnas entre ArcGIS Hub e HydroBASINS."""
    if source == "arcgis_hub":
        # El shapefile IDEAM suele traer NOM_ZH, COD_ZH, AH_COD, etc.
        candidatos_id = ["COD_SZH", "COD_ZH", "cod_szh", "cod_zh", "SZH", "ZH"]
        candidatos_nombre = ["NOM_SZH", "NOM_ZH", "nom_szh", "nombre_szh", "NOMBRE"]
        candidatos_area = ["NOM_AH", "AH", "area_hidro", "AREA_HIDRO"]

        col_id = next((c for c in candidatos_id if c in gdf.columns), None)
        col_nombre = next((c for c in candidatos_nombre if c in gdf.columns), None)
        col_area = next((c for c in candidatos_area if c in gdf.columns), None)

        gdf["id_cuenca"] = gdf[col_id].astype(str) if col_id else gdf.index.astype(str)
        gdf["nombre"] = gdf[col_nombre] if col_nombre else "Sin nombre"
        gdf["area_hidrografica"] = gdf[col_area] if col_area else "Sin clasificar"

    elif source == "hydrobasins":
        # HydroBASINS usa HYBAS_ID + atributos ordinales, no nombres.
        gdf["id_cuenca"] = gdf["HYBAS_ID"].astype(str)
        gdf["nombre"] = "HYBAS_" + gdf["HYBAS_ID"].astype(str)
        gdf["area_hidrografica"] = "HydroBASINS_L6"

    return gdf[["id_cuenca", "nombre", "area_hidrografica", "geometry"]].copy()
