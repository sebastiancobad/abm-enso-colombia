"""Tests de integraciÃ³n de la capa `data`.

Estos tests NO hacen llamadas de red reales. Usan:
- Fixtures locales (SIMMA CSV versionado)
- Monkeypatching de `requests.get` para ONI/cuencas
- Skip si las dependencias pesadas no estÃ¡n instaladas
"""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest


# ---------- Fixture global ----------
@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """Redirige las rutas de data/* a un directorio temporal."""
    from abm_enso.utils import paths

    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    raw.mkdir()
    processed.mkdir()

    monkeypatch.setattr(paths, "DATA_RAW", raw)
    monkeypatch.setattr(paths, "DATA_PROCESSED", processed)
    monkeypatch.setattr(paths, "ONI_CSV", raw / "oni_mensual.csv")
    monkeypatch.setattr(paths, "SIMMA_CSV", raw / "Resultados_SIMMA.csv")
    monkeypatch.setattr(paths, "CUENCAS_GPKG", raw / "cuencas.gpkg")
    monkeypatch.setattr(paths, "ERA5_CONSOLIDADO", processed / "era5_consolidado.csv")
    return tmp_path


# ==========================================================
# ONI
# ==========================================================
SAMPLE_ONI_TEXT = """SEAS  YR  TOTAL  ANOM
DJF  2020  26.16  0.53
JFM  2020  26.52  0.42
FMA  2020  27.15  0.18
MAM  2020  27.82  -0.12
AMJ  2020  27.90  -0.35
MJJ  2020  27.64  -0.53
JJA  2020  27.12  -0.58
JAS  2020  26.86  -0.95
ASO  2020  26.58  -1.25
SON  2020  26.31  -1.42
OND  2020  26.08  -1.38
NDJ  2020  25.99  -1.22
DJF  2021  25.98  -0.95
"""


def test_oni_parse_noaa_ascii():
    """El parser acepta el formato real de NOAA/CPC."""
    from abm_enso.data.oni import _parse_noaa_ascii

    df = _parse_noaa_ascii(SAMPLE_ONI_TEXT)

    assert "oni" in df.columns
    assert df.index.name == "fecha"
    assert pd.api.types.is_datetime64_any_dtype(df.index)
    assert len(df) == 13
    assert df["oni"].min() < 0
    assert df["oni"].max() > 0
    # Sanity: valores dentro del rango fÃ­sico ENSO
    assert df["oni"].abs().max() < 5


def test_oni_download_usa_cache(tmp_data_dir, monkeypatch):
    """Si el CSV ya existe y force=False, no hace request."""
    from abm_enso.data import oni
    from abm_enso.utils import paths

    # Pre-crear el CSV
    paths.ONI_CSV.write_text("fecha,oni\n2020-01-01,0.5\n")

    # Cualquier llamada a requests.get debe fallar el test
    def _mock_get(*a, **kw):
        raise AssertionError("No deberÃ­a llamar a la red cuando hay cache")
    monkeypatch.setattr("requests.get", _mock_get)

    result = oni.download(out_path=paths.ONI_CSV, force=False)
    assert result == paths.ONI_CSV


def test_oni_download_respeta_force(tmp_data_dir, monkeypatch):
    """Con force=True, re-descarga aunque exista cache."""
    from abm_enso.data import oni
    from abm_enso.utils import paths

    paths.ONI_CSV.write_text("contenido_viejo")

    mock_resp = MagicMock()
    mock_resp.text = SAMPLE_ONI_TEXT
    mock_resp.raise_for_status = lambda: None
    monkeypatch.setattr("requests.get", lambda *a, **kw: mock_resp)

    result = oni.download(out_path=paths.ONI_CSV, force=True)
    assert result.exists()
    # Debe haber sobrescrito
    df = pd.read_csv(result, index_col="fecha")
    assert "oni" in df.columns


# ==========================================================
# SIMMA
# ==========================================================
def test_simma_fallback_a_local_cuando_sgc_falla(tmp_data_dir, monkeypatch):
    """Si el endpoint SGC falla, usa el CSV PDF-extract local."""
    from abm_enso.data import simma
    from abm_enso.utils import paths
    import requests

    # Crear fallback local
    paths.SIMMA_CSV.write_text(encoding="utf-8", data=
        "Tipo movimiento,Fecha evento,Departamento,Municipio,Longitud (Â°)\n"
        "Deslizamiento,2023-01-15,BOYACÃ,TUNJA,-73.36\n"
    )

    # Mock de requests.get que lanza ConnectionError
    def _mock_get(*a, **kw):
        raise requests.ConnectionError("simulated")
    monkeypatch.setattr("requests.get", _mock_get)

    result = simma.download()
    assert result == paths.SIMMA_CSV


def test_simma_load_normaliza_nombres(tmp_data_dir):
    """Corrige 'CUNDINAMA RCA' â†’ 'CUNDINAMARCA' y normaliza columnas."""
    from abm_enso.data import simma
    from abm_enso.utils import paths

    paths.SIMMA_CSV.write_text(encoding="utf-8", data=
        "Tipo movimiento,Fecha evento,Departamento,Longitud (Â°)\n"
        "Deslizamiento,2023-01-15,CUNDINAMA RCA,-74.0\n"
        "Flujo,2015-03-10,MAGDALEN A,-74.5\n"
    )

    df = simma.load(auto_download=False)

    assert "tipo_movimiento" in df.columns
    assert "departamento" in df.columns
    assert "longitud" in df.columns
    assert "CUNDINAMARCA" in df["departamento"].values
    assert "MAGDALENA" in df["departamento"].values


def test_simma_load_filtra_por_tipo_y_anio(tmp_data_dir):
    """Los filtros `tipo` y rangos temporales funcionan."""
    from abm_enso.data import simma
    from abm_enso.utils import paths

    paths.SIMMA_CSV.write_text(encoding="utf-8", data=
        "Tipo movimiento,Fecha evento,Departamento,Longitud (Â°)\n"
        "Deslizamiento,2010-10-15,ANTIOQUIA,-75.0\n"
        "Flujo,2015-03-10,CAUCA,-76.0\n"
        "Deslizamiento,2023-01-15,BOYACA,-73.0\n"
    )

    df_desliz = simma.load(tipo="Deslizamiento", auto_download=False)
    assert len(df_desliz) == 2

    df_2010 = simma.load(anio_min=2010, anio_max=2015, auto_download=False)
    assert len(df_2010) == 2


# ==========================================================
# ERA5 (sin tocar xarray si no estÃ¡)
# ==========================================================
def test_era5_load_lee_consolidado_existente(tmp_data_dir):
    """Si existe el CSV consolidado, lo lee directamente sin tocar NetCDF."""
    from abm_enso.data import era5
    from abm_enso.utils import paths

    paths.ERA5_CONSOLIDADO.write_text(
        "fecha,precip_mm_mes,runoff_mm_mes,humedad_suelo_pct\n"
        "1981-01-01,120.5,45.2,28.3\n"
        "1981-02-01,180.1,72.4,30.1\n"
    )

    df = era5.load()
    assert "precip_mm_mes" in df.columns
    assert len(df) == 2


def test_era5_load_variable_individual(tmp_data_dir):
    """El argumento `variable=` filtra a la columna esperada."""
    from abm_enso.data import era5
    from abm_enso.utils import paths

    paths.ERA5_CONSOLIDADO.write_text(
        "fecha,precip_mm_mes,runoff_mm_mes,humedad_suelo_pct\n"
        "1981-01-01,120.5,45.2,28.3\n"
    )

    df_tp = era5.load(variable="tp")
    assert list(df_tp.columns) == ["precip_mm_mes"]


# ==========================================================
# Cuencas
# ==========================================================
def test_cuencas_sin_archivo_y_sin_auto_download_falla(tmp_data_dir):
    """Si no existe el GPKG y auto_download=False, FileNotFoundError."""
    from abm_enso.data import cuencas

    pytest.importorskip("geopandas")

    with pytest.raises(FileNotFoundError):
        cuencas.load(auto_download=False)


# ==========================================================
# Pipeline orquestador
# ==========================================================
def test_pipeline_descarga_fuente_desconocida():
    """El orquestador marca fuentes desconocidas como desconocida sin crashear."""
    from abm_enso.pipeline import descargar_todas

    results = descargar_todas(solo=["fuente_inexistente"], skip_on_error=True)
    assert "fuente_inexistente" in results
    ok, info = results["fuente_inexistente"]
    assert ok is False
    assert "desconocida" in info


def test_pipeline_lista_de_fuentes_disponibles():
    """Las 5 fuentes estÃ¡n registradas y en el orden esperado."""
    from abm_enso.pipeline import FUENTES_DISPONIBLES

    assert FUENTES_DISPONIBLES == ("oni", "era5", "sirh", "simma", "cuencas")

