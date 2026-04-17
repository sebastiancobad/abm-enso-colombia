"""Smoke tests: verifican que el paquete está bien estructurado.

En Fase 1 solo probamos que los módulos importan sin errores y que
las constantes tienen los tipos y rangos esperados. Tests de lógica
real llegan en fases posteriores.
"""

from __future__ import annotations


def test_paquete_importa():
    import abm_enso

    assert abm_enso.__version__ == "0.4.0"


def test_subpaquetes_importan():
    from abm_enso import analysis, data, model, utils, viz  # noqa: F401


def test_constantes_rangos():
    from abm_enso.utils import constants as C

    assert -90 < C.COLOMBIA_BBOX[1] < C.COLOMBIA_BBOX[3] < 90
    assert -180 < C.COLOMBIA_BBOX[0] < C.COLOMBIA_BBOX[2] < 180
    assert C.YEAR_START < C.YEAR_CALIBRATION_END < C.YEAR_END
    assert C.UMBRAL_NINA < 0 < C.UMBRAL_NINO
    assert 0 < C.THETA_DEFAULT < 1
    assert 0 < C.KAPPA_DEFAULT < 1
    assert set(C.BETA1_DEFAULT) == set(C.TIPOS_SUELO)


def test_paths_raiz_existe():
    from abm_enso.utils.paths import ROOT

    assert ROOT.exists()
    assert (ROOT / "pyproject.toml").exists()
    assert (ROOT / "README.md").exists()
