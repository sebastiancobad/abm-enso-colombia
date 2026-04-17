"""Tests de la capa `analysis` con datos sintéticos en runtime.

Estos tests NO leen archivos del disco. Generan series ad-hoc para validar
las propiedades matemáticas de cada módulo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def oni_sintetico():
    """Serie ONI sintética: coseno con período 4.5 años + ruido pequeño."""
    rng = np.random.default_rng(42)
    fechas = pd.date_range("1980-01", periods=540, freq="MS")  # 45 años
    t = np.arange(540)
    # Oscilación principal 4.5 años + armónico 2.25 años + ruido
    signal = (
        1.2 * np.cos(2 * np.pi * t / 54)
        + 0.4 * np.cos(2 * np.pi * t / 27)
        + 0.3 * rng.standard_normal(540)
    )
    return pd.Series(signal, index=fechas, name="oni")


@pytest.fixture
def precip_sintetica(oni_sintetico):
    """Precipitación con climatología + respuesta a ONI + ruido."""
    rng = np.random.default_rng(7)
    fechas = oni_sintetico.index
    # Climatología bimodal colombiana (picos en abr-may y oct-nov)
    clim = 150 + 80 * np.sin(2 * np.pi * fechas.month / 12 + np.pi / 2)
    clim += 40 * np.sin(4 * np.pi * fechas.month / 12)
    # Respuesta a ONI: β₁ = 25 mm/mes por °C
    beta_1_real = 25.0
    precip = clim + beta_1_real * oni_sintetico.values + 20 * rng.standard_normal(540)
    precip = np.maximum(precip, 0)  # no negativos
    return pd.Series(precip, index=fechas, name="precip")


# ==========================================================
# filtros
# ==========================================================
class TestFiltros:

    def test_butterworth_conserva_longitud(self, oni_sintetico):
        from abm_enso.analysis.filtros import butterworth_enso

        filtrada = butterworth_enso(oni_sintetico)
        assert len(filtrada) == len(oni_sintetico)
        assert filtrada.index.equals(oni_sintetico.index)

    def test_butterworth_atenua_alta_frecuencia(self, oni_sintetico):
        """La señal filtrada debe tener menor varianza que la original
        (porque quitamos ruido de alta frecuencia)."""
        from abm_enso.analysis.filtros import butterworth_enso

        filtrada = butterworth_enso(oni_sintetico)
        # El ruido gaussiano (alta frecuencia) se va
        assert filtrada.var() < oni_sintetico.var()

    def test_butterworth_rechaza_nan(self, oni_sintetico):
        from abm_enso.analysis.filtros import butterworth_enso

        with_nan = oni_sintetico.copy()
        with_nan.iloc[[10, 20, 30]] = np.nan

        with pytest.raises(ValueError, match="NaN"):
            butterworth_enso(with_nan)

    def test_butterworth_serie_muy_corta(self):
        from abm_enso.analysis.filtros import butterworth_enso

        corta = pd.Series(np.random.randn(5), index=pd.date_range("2020-01", periods=5, freq="MS"))
        with pytest.raises(ValueError, match="muy corta"):
            butterworth_enso(corta)

    def test_desestacionalizar_quita_media_por_mes(self):
        from abm_enso.analysis.filtros import desestacionalizar

        # Serie con perfecta estacionalidad
        fechas = pd.date_range("2020-01", periods=36, freq="MS")
        valores = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] * 3  # año = valor del mes
        serie = pd.Series(valores, index=fechas)

        anom = desestacionalizar(serie)
        # Todas las anomalías deben ser 0 (cada mes se repite igual)
        assert np.allclose(anom.values, 0.0, atol=1e-10)

    def test_filtrar_fuente_pipeline_completo(self, precip_sintetica):
        from abm_enso.analysis.filtros import filtrar_fuente

        filtrada = filtrar_fuente(precip_sintetica, quitar_clima=True)
        # Tras desestacionalizar, la media debe ser ~0
        assert abs(filtrada.mean()) < 1.0


# ==========================================================
# lorenz
# ==========================================================
class TestLorenz:

    def test_integrar_produce_atractor(self):
        from abm_enso.analysis.lorenz import integrar

        sol = integrar(T=50.0, dt=0.01, skip_transient=1000)
        # El atractor de Lorenz tiene rangos conocidos aproximados
        assert sol.shape[1] == 3
        assert (sol[:, 0].max() - sol[:, 0].min()) > 20   # x oscila en rango grande
        assert 0 < sol[:, 2].min() < 50  # z es siempre positivo

    def test_integrar_es_reproducible(self):
        from abm_enso.analysis.lorenz import integrar

        sol1 = integrar(T=20.0, dt=0.01, init=(1.0, 1.0, 1.0))
        sol2 = integrar(T=20.0, dt=0.01, init=(1.0, 1.0, 1.0))
        assert np.allclose(sol1, sol2)

    def test_calibrar_a_oni_preserva_media_y_std(self, oni_sintetico):
        from abm_enso.analysis.filtros import butterworth_enso
        from abm_enso.analysis.lorenz import calibrar_a_oni, integrar

        oni_filt = butterworth_enso(oni_sintetico)
        sol = integrar(T=200.0, dt=0.01)
        oni_lorenz = calibrar_a_oni(sol[:, 0], oni_filt)

        # Tras calibrar, media y std deben ser cercanas al ONI original
        assert abs(oni_lorenz.mean() - oni_filt.mean()) < 0.1
        assert abs(oni_lorenz.std() - oni_filt.std()) < 0.2

    def test_generar_oni_sintetico_pipeline(self, oni_sintetico):
        from abm_enso.analysis.filtros import butterworth_enso
        from abm_enso.analysis.lorenz import generar_oni_sintetico

        oni_filt = butterworth_enso(oni_sintetico)
        oni_sint = generar_oni_sintetico(oni_filt, T=500.0, seed=42)

        assert len(oni_sint) == len(oni_filt)
        assert oni_sint.index.equals(oni_filt.index)
        # El ONI sintético debe tener rango "ENSO-like" (-3 a +3)
        assert oni_sint.abs().max() < 5


# ==========================================================
# calibracion_beta
# ==========================================================
class TestCalibracionBeta:

    def test_ols_beta1_recupera_pendiente_conocida(self, oni_sintetico, precip_sintetica):
        from abm_enso.analysis.calibracion_beta import ols_beta1
        from abm_enso.analysis.filtros import desestacionalizar

        precip_anom = desestacionalizar(precip_sintetica)
        resultado = ols_beta1(oni_sintetico, precip_anom)

        # β_1 real era 25, deberíamos recuperar algo cercano
        assert 20 < resultado["beta_1"] < 30
        assert resultado["r"] > 0.7   # ruido sintético limita r máximo
        assert resultado["n"] > 100

    def test_ols_beta1_rechaza_pocos_puntos(self):
        from abm_enso.analysis.calibracion_beta import ols_beta1

        cortos_a = pd.Series([1, 2, 3])
        cortos_b = pd.Series([10, 20, 30])

        with pytest.raises(ValueError, match="pocos puntos"):
            ols_beta1(cortos_a, cortos_b)


# ==========================================================
# calibracion_theta_kappa
# ==========================================================
class TestCalibracionThetaKappa:

    def test_simular_eventos_precip_cero_no_activa(self):
        from abm_enso.analysis.calibracion_theta_kappa import simular_eventos

        precip_cero = np.zeros(50)
        eventos = simular_eventos(precip_cero, theta=0.5, kappa=0.2, capacidad=1000.0)
        assert not eventos.any()

    def test_simular_eventos_precip_alta_activa(self):
        from abm_enso.analysis.calibracion_theta_kappa import simular_eventos

        # Si metes 1000 mm/mes durante 3 meses, debes activar el umbral
        precip = np.full(20, 1000.0)
        eventos = simular_eventos(precip, theta=0.5, kappa=0.2, capacidad=1000.0)
        assert eventos.any()

    def test_grid_search_encuentra_optimo(self):
        from abm_enso.analysis.calibracion_theta_kappa import (
            grid_search_f1,
            simular_eventos,
        )

        # Generar datos con θ=0.80, κ=0.20 conocidos
        rng = np.random.default_rng(42)
        precip = 100 + 200 * rng.random(200)
        eventos_true = simular_eventos(precip, theta=0.80, kappa=0.20, capacidad=1000.0)

        resultado = grid_search_f1(
            precip, eventos_true,
            theta_grid=np.arange(0.7, 0.9, 0.05),
            kappa_grid=np.arange(0.1, 0.3, 0.05),
        )

        # El grid search debería encontrar el óptimo o cercano
        assert abs(resultado.theta_opt - 0.80) <= 0.05
        assert abs(resultado.kappa_opt - 0.20) <= 0.05
        assert resultado.f1_opt > 0.99  # casi perfecto porque los datos son exactos


# ==========================================================
# metricas
# ==========================================================
class TestMetricas:

    def test_pearson_r_series_iguales_es_uno(self):
        from abm_enso.analysis.metricas import pearson_r

        a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert pearson_r(a, a) == pytest.approx(1.0)

    def test_pearson_r_anticorrelacion(self):
        from abm_enso.analysis.metricas import pearson_r

        a = np.array([1.0, 2.0, 3.0])
        b = np.array([3.0, 2.0, 1.0])
        assert pearson_r(a, b) == pytest.approx(-1.0)

    def test_rmse_series_iguales_es_cero(self):
        from abm_enso.analysis.metricas import rmse

        a = np.array([1.0, 2.0, 3.0])
        assert rmse(a, a) == 0.0

    def test_f1_perfecto(self):
        from abm_enso.analysis.metricas import f1_score

        y_true = np.array([1, 0, 1, 1, 0])
        y_pred = np.array([1, 0, 1, 1, 0])
        assert f1_score(y_true, y_pred) == 1.0

    def test_f1_predicciones_vacias(self):
        from abm_enso.analysis.metricas import f1_score

        y_true = np.array([1, 1, 0, 0])
        y_pred = np.array([0, 0, 0, 0])
        assert f1_score(y_true, y_pred) == 0.0

    def test_lomb_scargle_detecta_periodicidad(self):
        from abm_enso.analysis.metricas import lomb_scargle

        # Señal 1/(4 años) = 0.25 cycles/year
        fechas = pd.date_range("1980-01", periods=540, freq="MS")
        t_years = (fechas - fechas[0]).days / 365.25
        serie = pd.Series(np.cos(2 * np.pi * t_years / 4), index=fechas)

        freqs, power = lomb_scargle(serie, f_min_cycles_per_year=0.1, f_max_cycles_per_year=1.0)
        pico = freqs[np.argmax(power)]
        assert abs(pico - 0.25) < 0.03
