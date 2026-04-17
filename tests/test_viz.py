"""Tests del subpaquete viz.

Los componentes Solara no se pueden testear unitariamente sin navegador;
estos tests cubren lógica pura (SimulacionEnVivo, render helpers, export).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def gdf_cuencas_sinteticas():
    """GeoDataFrame mínimo con 5 cuencas."""
    try:
        import geopandas as gpd
        from shapely.geometry import Polygon
    except ImportError:
        pytest.skip("geopandas no disponible")

    polys = [
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
        Polygon([(0, 1), (1, 1), (1, 2), (0, 2)]),
        Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
        Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),
    ]
    gdf = gpd.GeoDataFrame(
        {
            "id_cuenca": [f"C{i:03d}" for i in range(5)],
            "area_hidrografica": ["Caribe", "Magdalena-Cauca", "Pacifico", "Orinoco", "Amazonas"],
            "area_km2": [100.0, 150.0, 80.0, 120.0, 200.0],
        },
        geometry=polys,
        crs="EPSG:4326",
    )
    return gdf


class TestSimulacionEnVivo:

    def test_crear_sin_modelo(self, gdf_cuencas_sinteticas):
        from abm_enso.viz.simulacion import SimulacionEnVivo
        sim = SimulacionEnVivo(gdf_cuencas_sinteticas)
        assert sim.modelo is None
        assert sim.tick() == 0

    def test_reset_con_escenario_neutro(self, gdf_cuencas_sinteticas):
        from abm_enso.viz.simulacion import ParametrosSimulacion, SimulacionEnVivo
        sim = SimulacionEnVivo(gdf_cuencas_sinteticas)
        sim.reset_con_escenario(ParametrosSimulacion(escenario="neutro", n_meses=24, seed=1))
        assert sim.modelo is not None
        assert sim.n_meses() == 24

    def test_step_avanza_tick(self, gdf_cuencas_sinteticas):
        from abm_enso.viz.simulacion import ParametrosSimulacion, SimulacionEnVivo
        sim = SimulacionEnVivo(gdf_cuencas_sinteticas)
        sim.reset_con_escenario(ParametrosSimulacion(escenario="neutro", n_meses=24, seed=1))
        assert sim.tick() == 0
        sim.step()
        assert sim.tick() == 1

    def test_step_retorna_false_al_fin(self, gdf_cuencas_sinteticas):
        from abm_enso.viz.simulacion import ParametrosSimulacion, SimulacionEnVivo
        sim = SimulacionEnVivo(gdf_cuencas_sinteticas)
        sim.reset_con_escenario(ParametrosSimulacion(escenario="neutro", n_meses=3, seed=1))
        for _ in range(3):
            assert sim.step() is True
        assert sim.step() is False

    def test_snapshot_estado_tiene_columnas_esperadas(self, gdf_cuencas_sinteticas):
        from abm_enso.viz.simulacion import ParametrosSimulacion, SimulacionEnVivo
        sim = SimulacionEnVivo(gdf_cuencas_sinteticas)
        sim.reset_con_escenario(ParametrosSimulacion(escenario="neutro", n_meses=12, seed=1))
        sim.step()
        snap = sim.snapshot_estado()
        assert "id_cuenca" in snap.columns
        assert "estado" in snap.columns
        assert len(snap) == 5
        assert set(snap["estado"].unique()) <= {"estiaje", "normal", "humedo", "saturado"}

    def test_snapshot_series_incluye_oni(self, gdf_cuencas_sinteticas):
        from abm_enso.viz.simulacion import ParametrosSimulacion, SimulacionEnVivo
        sim = SimulacionEnVivo(gdf_cuencas_sinteticas)
        sim.reset_con_escenario(ParametrosSimulacion(escenario="neutro", n_meses=12, seed=1))
        for _ in range(5):
            sim.step()
        series = sim.snapshot_series()
        assert "oni" in series.columns
        assert "activaciones_pct" in series.columns
        assert len(series) == 5

    def test_escenario_desconocido_falla(self, gdf_cuencas_sinteticas):
        from abm_enso.viz.simulacion import ParametrosSimulacion, SimulacionEnVivo
        sim = SimulacionEnVivo(gdf_cuencas_sinteticas)
        with pytest.raises(ValueError, match="Escenario desconocido"):
            sim.reset_con_escenario(ParametrosSimulacion(escenario="inexistente"))


class TestMapa:

    def test_dibujar_mapa_sin_estado(self, gdf_cuencas_sinteticas):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from abm_enso.viz.mapa_cuencas import dibujar_mapa
        fig = dibujar_mapa(gdf_cuencas_sinteticas, df_estado=None)
        assert fig is not None
        plt.close(fig)

    def test_dibujar_mapa_con_estado(self, gdf_cuencas_sinteticas):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from abm_enso.viz.mapa_cuencas import dibujar_mapa
        df_estado = pd.DataFrame({
            "id_cuenca": [f"C{i:03d}" for i in range(5)],
            "estado": ["estiaje", "normal", "humedo", "saturado", "normal"],
        })
        fig = dibujar_mapa(gdf_cuencas_sinteticas, df_estado=df_estado, titulo="Test")
        assert fig is not None
        plt.close(fig)

    def test_dibujar_mapa_a_buffer_devuelve_png_bytes(self, gdf_cuencas_sinteticas):
        import matplotlib
        matplotlib.use("Agg")
        from abm_enso.viz.mapa_cuencas import dibujar_mapa_a_buffer
        png = dibujar_mapa_a_buffer(gdf_cuencas_sinteticas, df_estado=None, dpi=60)
        assert png.startswith(b"\x89PNG")


class TestPaneles:

    def test_series_vacias_no_crashean(self):
        from abm_enso.viz.series import dibujar_series
        fig = dibujar_series(pd.DataFrame(), escenario="neutro")
        assert fig is not None

    def test_heatmap_vacio_no_crashea(self):
        from abm_enso.viz.heatmap import dibujar_heatmap
        fig = dibujar_heatmap(pd.DataFrame())
        assert fig is not None

    def test_periodograma_serie_corta_no_crashea(self):
        from abm_enso.viz.periodograma import dibujar_periodograma
        df = pd.DataFrame({
            "activaciones_pct": np.random.rand(10) * 10,
        }, index=pd.date_range("2020-01", periods=10, freq="MS"))
        fig = dibujar_periodograma(df)
        assert fig is not None

    def test_periodograma_detecta_periodicidad(self):
        from abm_enso.viz.periodograma import dibujar_periodograma
        fechas = pd.date_range("1980-01", periods=240, freq="MS")
        t_years = (fechas - fechas[0]).days / 365.25
        df = pd.DataFrame({
            "activaciones_pct": 50 + 20 * np.cos(2 * np.pi * t_years / 4),
        }, index=fechas)
        fig = dibujar_periodograma(df)
        assert fig is not None


class TestExport:

    def test_ffmpeg_disponible_devuelve_bool(self):
        from abm_enso.viz.export import ffmpeg_disponible
        assert isinstance(ffmpeg_disponible(), bool)
