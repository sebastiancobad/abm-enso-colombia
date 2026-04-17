"""Generadores de forzamiento ONI para escenarios pre-configurados.

Un escenario es una serie temporal de valores ONI mensuales que alimenta
el ABM como forzamiento externo. Cada escenario representa una condición
climática de interés:

    nina-2010   → La Niña fuerte 2010-2012 (inundaciones Colombia)
    nino-2015   → El Niño extremo 2015-2016 (sequía histórica)
    neutro      → ONI ≈ 0 constante (control)
    lorenz      → serie sintética determinística del atractor de Lorenz
    historico   → ONI real observado de NOAA
    custom      → función arbitraria del tiempo

Funciones públicas:
    escenario_nina_2010(n_meses)       → Serie con pico La Niña
    escenario_nino_2015(n_meses)
    escenario_neutro(n_meses)
    escenario_historico(inicio, fin)   → ONI real de disco
    escenario_lorenz(n_meses, seed)    → ONI sintético
    escenario_custom(func, inicio)     → f(t) → ONI
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable

import numpy as np
import pandas as pd


def _fechas_desde(inicio: str, n_meses: int) -> pd.DatetimeIndex:
    """Genera un DatetimeIndex mensual (frecuencia 'MS')."""
    return pd.date_range(start=inicio, periods=n_meses, freq="MS")


# ==========================================================
# Escenarios idealizados
# ==========================================================
def escenario_nina_2010(
    n_meses: int = 36,
    pico: float = -1.6,
    mes_pico: int = 12,
    inicio: str = "2010-01-01",
) -> pd.Series:
    """La Niña fuerte centrada en mes_pico.

    Usa una curva gaussiana: ONI(t) = pico · exp(-(t - mes_pico)² / 2σ²)
    con σ = 6 meses, simulando el evento La Niña 2010-2011 que generó
    inundaciones históricas en Colombia.
    """
    t = np.arange(n_meses)
    sigma = 6.0
    oni = pico * np.exp(-((t - mes_pico) ** 2) / (2 * sigma ** 2))
    return pd.Series(oni, index=_fechas_desde(inicio, n_meses), name="oni")


def escenario_nino_2015(
    n_meses: int = 36,
    pico: float = +2.3,
    mes_pico: int = 18,
    inicio: str = "2015-01-01",
) -> pd.Series:
    """El Niño extremo 2015-2016 (récord histórico del Pacífico)."""
    t = np.arange(n_meses)
    sigma = 7.0
    oni = pico * np.exp(-((t - mes_pico) ** 2) / (2 * sigma ** 2))
    return pd.Series(oni, index=_fechas_desde(inicio, n_meses), name="oni")


def escenario_neutro(
    n_meses: int = 36,
    inicio: str = "2000-01-01",
    jitter: float = 0.1,
    seed: int = 42,
) -> pd.Series:
    """ONI ≈ 0 con pequeño ruido — control ENSO-neutral."""
    rng = np.random.default_rng(seed)
    oni = rng.normal(0.0, jitter, size=n_meses)
    return pd.Series(oni, index=_fechas_desde(inicio, n_meses), name="oni")


# ==========================================================
# Escenarios basados en datos
# ==========================================================
def escenario_historico(
    inicio: str = "2010-01-01",
    fin: str = "2012-12-31",
) -> pd.Series:
    """ONI observado real (NOAA) entre ``inicio`` y ``fin``.

    Sirve para validación: corres el modelo con el ONI de 2010-2012 y
    comparas activaciones simuladas vs eventos SIMMA del mismo período.
    """
    from abm_enso.data import oni as oni_mod
    df = oni_mod.load()
    return df.loc[inicio:fin, "oni"].dropna().rename("oni")


def escenario_lorenz(
    n_meses: int = 540,
    seed: int = 42,
    inicio: str = "1980-01-01",
) -> pd.Series:
    """ONI sintético del sistema de Lorenz, calibrado al ONI real.

    Genera ``n_meses`` de datos deterministas pero caóticos cuyas
    propiedades estadísticas (media, std, varianza) coinciden con el
    ONI observado. Útil para proyecciones ENSO más allá de los datos.
    """
    from abm_enso.analysis import filtros, lorenz
    from abm_enso.data import oni as oni_mod

    df_real = oni_mod.load()["oni"].dropna()
    oni_filt = filtros.butterworth_enso(df_real)

    # Generar una serie larga y recortar a n_meses
    oni_sint = lorenz.generar_oni_sintetico(oni_filt, T=3000.0, seed=seed)
    if len(oni_sint) < n_meses:
        raise ValueError(f"Lorenz generó {len(oni_sint)} < {n_meses} meses")

    serie = oni_sint.iloc[:n_meses]
    serie.index = _fechas_desde(inicio, n_meses)
    serie.name = "oni"
    return serie


# ==========================================================
# Escenario arbitrario
# ==========================================================
def escenario_custom(
    func: Callable[[int], float],
    n_meses: int = 36,
    inicio: str = "2000-01-01",
) -> pd.Series:
    """Serie ONI construida aplicando ``func(t)`` para t = 0..n_meses-1."""
    vals = np.array([func(t) for t in range(n_meses)], dtype=float)
    return pd.Series(vals, index=_fechas_desde(inicio, n_meses), name="oni")


# ==========================================================
# Registry para la CLI
# ==========================================================
ESCENARIOS_DISPONIBLES: dict[str, Callable[..., pd.Series]] = {
    "nina-2010":  escenario_nina_2010,
    "nino-2015":  escenario_nino_2015,
    "neutro":     escenario_neutro,
    "historico":  escenario_historico,
    "lorenz":     escenario_lorenz,
}


def get(nombre: str) -> Callable[..., pd.Series]:
    """Retorna el generador de escenario por nombre."""
    if nombre not in ESCENARIOS_DISPONIBLES:
        raise ValueError(
            f"Escenario '{nombre}' no existe. "
            f"Disponibles: {list(ESCENARIOS_DISPONIBLES)}"
        )
    return ESCENARIOS_DISPONIBLES[nombre]
