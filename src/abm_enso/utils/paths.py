"""Rutas canónicas del proyecto.

Todas las rutas se resuelven relativas a la raíz del repo, detectada
automáticamente a partir de la ubicación de este archivo. Importar desde
aquí evita `../../data/...` frágiles en notebooks y scripts.
"""

from __future__ import annotations

from pathlib import Path

# ---- Raíz del repo ----
# src/abm_enso/utils/paths.py  →  subir 4 niveles
ROOT = Path(__file__).resolve().parents[3]

# ---- Datos ----
DATA_DIR = ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_EXTERNAL = DATA_DIR / "external"

# ---- Archivos específicos de entrada ----
ONI_CSV = DATA_RAW / "oni_mensual.csv"
ERA5_NC_FLUJOS = DATA_RAW / "era5_stepType-avgad.nc"   # tp, ro
ERA5_NC_ESTADO = DATA_RAW / "era5_stepType-avgua.nc"   # swvl1
SIRH_CSV = DATA_RAW / "nivel_sirh_diario.csv"
SIMMA_CSV = DATA_RAW / "Resultados_SIMMA.csv"
CUENCAS_GPKG = DATA_RAW / "cuencas_colombia.gpkg"

# ---- Archivos procesados ----
ERA5_CONSOLIDADO = DATA_PROCESSED / "era5_colombia_consolidado.csv"
ONI_FILTRADO = DATA_PROCESSED / "oni_enso_butterworth.csv"
LORENZ_SIMULADO = DATA_PROCESSED / "oni_lorenz.csv"
CUENCAS_CALIBRADAS = DATA_PROCESSED / "cuencas_parametros.parquet"

# ---- Outputs ----
OUTPUTS_DIR = ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
SIMULATIONS_DIR = OUTPUTS_DIR / "simulations"

# ---- Documentación y notebooks ----
DOCS_DIR = ROOT / "docs"
NOTEBOOKS_DIR = ROOT / "notebooks"


def ensure_dirs() -> None:
    """Crea todos los directorios requeridos si no existen."""
    for d in [
        DATA_RAW,
        DATA_PROCESSED,
        DATA_EXTERNAL,
        FIGURES_DIR,
        SIMULATIONS_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
