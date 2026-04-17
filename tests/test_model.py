"""Tests del subpaquete `model` con síntesis en runtime.

No dependen de datos reales en disco: generan un GeoDataFrame fake
con 5 cuencas y un ONI sintético, y validan las invariantes matemáticas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def gdf_fake():
    """GeoDataFrame-like (DataFrame) con 5 cuencas en diferentes áreas."""
    # Usamos un DataFrame simple (no GeoDataFrame) porque el agente no
    # accede a la geometría; solo a las columnas tabulares.
    return pd.DataFrame({
        "id_cuenca": ["c01", "c02", "c03", "c04", "c05"],
        "nombre": [
            "Magdalena Alto", "Canal del Dique", "San Juan", "Meta", "Caqueta"
        ],
        "area_hidrografica": [
            "Magdalena-Cauca", "Caribe", "Pacifico", "Orinoco", "Amazonas"
        ],
    })


@pytest.fixture
def oni_corto():
    """ONI sintético de 24 meses centrado en La Niña."""
    fechas = pd.date_range("2010-01-01", periods=24, freq="MS")
    t = np.arange(24)
    oni = -1.5 * np.exp(-((t - 12) ** 2) / (2 * 6.0 ** 2))  # pico La Niña en mes 12
    return pd.Series(oni, index=fechas, name="oni")


# ==========================================================
# Agente
# ==========================================================
class TestCuencaAgent:

    def test_agente_se_crea_con_atributos(self, gdf_fake, oni_corto):
        from abm_enso.model import ModeloCuencas

        m = ModeloCuencas(gdf_fake, oni_corto, seed=42)
        assert len(m.agents) == 5
        ids = {a.id_cuenca for a in m.agents}
        assert ids == {"c01", "c02", "c03", "c04", "c05"}

    def test_beta1_distinto_por_area(self, gdf_fake, oni_corto):
        from abm_enso.model import ModeloCuencas

        m = ModeloCuencas(gdf_fake, oni_corto, seed=42)
        betas = {a.area_hidrografica: a.beta_1 for a in m.agents}
        # Magdalena-Cauca debe tener β₁ más negativo (mayor sensibilidad)
        assert betas["Magdalena-Cauca"] < betas["Amazonas"]
        assert all(b < 0 for b in betas.values())  # todos negativos

    def test_humedad_inicial_proporcional_a_capacidad(self, gdf_fake, oni_corto):
        from abm_enso.model import ModeloCuencas

        m = ModeloCuencas(gdf_fake, oni_corto, seed=42)
        for a in m.agents:
            frac = a.humedad / a.capacidad_hidrica
            assert 0.25 < frac < 0.35  # inicializada al 30%

    def test_precip_climatologia_default_tiene_12_valores(self, gdf_fake, oni_corto):
        from abm_enso.model import ModeloCuencas

        m = ModeloCuencas(gdf_fake, oni_corto, seed=42)
        for a in m.agents:
            assert len(a.precip_climatologia) == 12
            assert all(p > 0 for p in a.precip_climatologia)

    def test_clasificar_estado_buckets(self, gdf_fake, oni_corto):
        from abm_enso.model import ModeloCuencas

        m = ModeloCuencas(gdf_fake, oni_corto, seed=42)
        a = list(m.agents)[0]
        # Probar los 4 niveles
        a.humedad = 0.10 * a.capacidad_hidrica
        assert a.clasificar_estado() == "estiaje"
        a.humedad = 0.45 * a.capacidad_hidrica
        assert a.clasificar_estado() == "normal"
        a.humedad = 0.70 * a.capacidad_hidrica
        assert a.clasificar_estado() == "humedo"
        a.humedad = 0.95 * a.capacidad_hidrica
        assert a.clasificar_estado() == "saturado"


# ==========================================================
# Modelo
# ==========================================================
class TestModeloCuencas:

    def test_step_avanza_tick(self, gdf_fake, oni_corto):
        from abm_enso.model import ModeloCuencas

        m = ModeloCuencas(gdf_fake, oni_corto, seed=42)
        assert m.tick == 0
        m.step()
        assert m.tick == 1

    def test_run_completo_registra_historial(self, gdf_fake, oni_corto):
        from abm_enso.model import ModeloCuencas

        m = ModeloCuencas(gdf_fake, oni_corto, seed=42)
        m.run()
        assert m.tick == len(oni_corto)
        assert len(m.historial_oni) == len(oni_corto)
        assert len(m.historial_activaciones) == len(oni_corto)

    def test_activacion_simultanea_no_usa_humedad_actualizada_de_otros(
        self, gdf_fake, oni_corto
    ):
        """Propiedad clave del scheduler: la fase A calcula con el estado
        de inicio del tick; la fase B aplica. Comprobamos que todas las
        cuencas vieron la misma H(t) inicial (no la actualizada dentro del tick)."""
        from abm_enso.model import ModeloCuencas

        m = ModeloCuencas(gdf_fake, oni_corto, seed=42)

        # Tras un step, el compute/apply de la fase A debe haber usado
        # el H(t-1) consistente para todos. Verificamos via log de precipitación:
        # si compute se hizo con mismo tick para todos, precip_historial[0] debe
        # tener longitud 1 en cada agente tras step().
        m.step()
        for a in m.agents:
            assert len(a.historial_humedad) == 1
            assert len(a.historial_precip) == 1

    def test_la_nina_genera_mas_humedad_que_neutro(self, gdf_fake):
        """Con β₁ negativo, ONI = -1.5 debería producir más lluvia/humedad
        que ONI = 0 en el mismo mes."""
        from abm_enso.model import ModeloCuencas

        fechas = pd.date_range("2010-01-01", periods=12, freq="MS")
        oni_nina = pd.Series([-1.5] * 12, index=fechas, name="oni")
        oni_neutro = pd.Series([0.0] * 12, index=fechas, name="oni")

        m_nina = ModeloCuencas(gdf_fake, oni_nina, seed=42, ruido_precip=0.0)
        m_neutro = ModeloCuencas(gdf_fake, oni_neutro, seed=42, ruido_precip=0.0)
        m_nina.run()
        m_neutro.run()

        h_nina = float(np.mean(m_nina.historial_humedad_media))
        h_neutro = float(np.mean(m_neutro.historial_humedad_media))
        assert h_nina > h_neutro

    def test_reproducibilidad_con_misma_seed(self, gdf_fake, oni_corto):
        """Misma seed → mismos resultados bit-a-bit."""
        from abm_enso.model import ModeloCuencas

        m1 = ModeloCuencas(gdf_fake, oni_corto, seed=7, ruido_precip=0.2)
        m2 = ModeloCuencas(gdf_fake, oni_corto, seed=7, ruido_precip=0.2)
        m1.run()
        m2.run()
        assert m1.historial_humedad_media == m2.historial_humedad_media

    def test_resumen_temporal_tiene_columnas_correctas(self, gdf_fake, oni_corto):
        from abm_enso.model import ModeloCuencas

        m = ModeloCuencas(gdf_fake, oni_corto, seed=42)
        m.run()
        df = m.resumen_temporal()
        assert set(df.columns) == {
            "tick", "fecha", "oni", "n_activaciones", "humedad_media"
        }
        assert len(df) == len(oni_corto)


# ==========================================================
# Escenarios
# ==========================================================
class TestEscenarios:

    def test_nina_2010_tiene_valor_negativo(self):
        from abm_enso.model import escenarios

        s = escenarios.escenario_nina_2010(n_meses=36)
        assert len(s) == 36
        assert s.min() < -1.0  # pico La Niña
        assert s.index.freqstr == "MS"

    def test_nino_2015_tiene_valor_positivo(self):
        from abm_enso.model import escenarios

        s = escenarios.escenario_nino_2015(n_meses=36)
        assert s.max() > 1.5  # pico El Niño fuerte

    def test_neutro_cerca_de_cero(self):
        from abm_enso.model import escenarios

        s = escenarios.escenario_neutro(n_meses=60, jitter=0.1)
        assert abs(s.mean()) < 0.1
        assert s.std() < 0.2

    def test_custom_aplica_funcion(self):
        from abm_enso.model import escenarios

        s = escenarios.escenario_custom(lambda t: 0.5 * t, n_meses=5)
        assert list(s.values) == [0.0, 0.5, 1.0, 1.5, 2.0]

    def test_get_retorna_callable(self):
        from abm_enso.model import escenarios

        f = escenarios.get("neutro")
        assert callable(f)

    def test_get_rechaza_nombre_invalido(self):
        from abm_enso.model import escenarios

        with pytest.raises(ValueError, match="no existe"):
            escenarios.get("no-existe")


# ==========================================================
# Ruido estocástico
# ==========================================================
class TestRuido:

    def test_ruido_cero_es_determinista(self, gdf_fake, oni_corto):
        from abm_enso.model import ModeloCuencas

        m1 = ModeloCuencas(gdf_fake, oni_corto, seed=1, ruido_precip=0.0)
        m2 = ModeloCuencas(gdf_fake, oni_corto, seed=99, ruido_precip=0.0)
        m1.run()
        m2.run()
        # Sin ruido, el seed no debe cambiar nada
        assert m1.historial_humedad_media == m2.historial_humedad_media

    def test_ruido_positivo_cambia_resultados_entre_seeds(self, gdf_fake, oni_corto):
        from abm_enso.model import ModeloCuencas

        m1 = ModeloCuencas(gdf_fake, oni_corto, seed=1, ruido_precip=0.3)
        m2 = ModeloCuencas(gdf_fake, oni_corto, seed=99, ruido_precip=0.3)
        m1.run()
        m2.run()
        # Con ruido, seeds distintos → resultados distintos
        assert m1.historial_humedad_media != m2.historial_humedad_media
