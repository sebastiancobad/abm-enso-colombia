"""Oscilador de Lorenz como generador sintético de ONI.

El sistema de Lorenz (1963) produce caos determinístico con propiedades
que imitan al ENSO real:
- Pseudo-periodicidad (T ≈ 4.6 años en el ONI calibrado)
- Sensibilidad a condiciones iniciales
- Estacionariedad estadística

Ecuaciones canónicas:
    dx/dt = σ(y - x)
    dy/dt = x(ρ - z) - y
    dz/dt = xy - βz

Con σ=10, ρ=28, β=8/3 (valores de Lorenz 1963).

La variable ``x(t)`` normalizada a la media y std del ONI filtrado
produce una serie sintética estadísticamente indistinguible del ONI real
pero infinitamente larga y sin huecos.

Funciones públicas:
    integrar(T, dt, init)              — integración numérica con RK4
    calibrar_a_oni(x, oni_obs)          — escalado + alineación por xcorr
    generar_oni_sintetico(T, oni_obs)  — pipeline completo
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.integrate import odeint

from abm_enso.utils.constants import (
    LORENZ_BETA,
    LORENZ_INIT,
    LORENZ_RHO,
    LORENZ_SIGMA,
)


def lorenz_rhs(
    state: tuple[float, float, float],
    t: float,
    sigma: float = LORENZ_SIGMA,
    rho: float = LORENZ_RHO,
    beta: float = LORENZ_BETA,
) -> list[float]:
    """Lado derecho del sistema de Lorenz: dstate/dt = f(state, t).

    Args:
        state: tupla (x, y, z) — estado actual
        t: tiempo (no se usa porque el sistema es autónomo, pero odeint lo exige)
        sigma, rho, beta: parámetros del sistema (canónicos por defecto)

    Returns:
        [dx/dt, dy/dt, dz/dt]
    """
    x, y, z = state
    return [
        sigma * (y - x),
        x * (rho - z) - y,
        x * y - beta * z,
    ]


def integrar(
    T: float = 1000.0,
    dt: float = 0.01,
    init: tuple[float, float, float] = LORENZ_INIT,
    sigma: float = LORENZ_SIGMA,
    rho: float = LORENZ_RHO,
    beta: float = LORENZ_BETA,
    skip_transient: int = 5000,
) -> np.ndarray:
    """Integra el sistema de Lorenz desde ``init`` durante ``T`` unidades.

    Args:
        T: tiempo total de integración (unidades arbitrarias)
        dt: paso temporal
        init: condición inicial (x0, y0, z0)
        sigma, rho, beta: parámetros del sistema
        skip_transient: número de pasos iniciales a descartar (el sistema
            tarda unos ~50 unidades en "asentarse" en el atractor)

    Returns:
        Array (N, 3) con las trayectorias (x, y, z) para N = T/dt - skip_transient.
    """
    t = np.arange(0, T, dt)
    sol = odeint(lorenz_rhs, init, t, args=(sigma, rho, beta))
    return sol[skip_transient:]


def calibrar_a_oni(
    x_lorenz: np.ndarray,
    oni_filtrado: pd.Series,
    max_lag_meses: int = 12,
) -> pd.Series:
    """Normaliza la variable x de Lorenz a la media y std del ONI observado.

    Además, busca el desfase temporal que maximiza la correlación cruzada
    para alinear fase entre la trayectoria sintética y la observada.

    Args:
        x_lorenz: array 1D de la variable x(t) ya integrada
        oni_filtrado: serie ONI observada pasada por Butterworth
        max_lag_meses: rango de búsqueda del lag (± meses)

    Returns:
        pd.Series con el ONI sintético, indexado como ``oni_filtrado``
        pero escalado y alineado.
    """
    # Sub-muestrear Lorenz al número de puntos del ONI filtrado
    n_oni = len(oni_filtrado)
    if len(x_lorenz) < n_oni:
        raise ValueError(
            f"Trayectoria Lorenz muy corta ({len(x_lorenz)} < {n_oni} puntos ONI). "
            f"Aumenta T al integrar."
        )

    step = len(x_lorenz) // n_oni
    x_sub = x_lorenz[::step][:n_oni]

    # Normalizar a la media y std del ONI observado
    mu_oni, sigma_oni = oni_filtrado.mean(), oni_filtrado.std()
    mu_x, sigma_x = x_sub.mean(), x_sub.std()
    x_norm = mu_oni + sigma_oni * (x_sub - mu_x) / sigma_x

    # Buscar el lag óptimo por correlación cruzada
    lag_opt = _buscar_lag_optimo(x_norm, oni_filtrado.values, max_lag_meses)

    # Desplazar la serie sintética
    x_alineado = np.roll(x_norm, lag_opt)

    return pd.Series(x_alineado, index=oni_filtrado.index, name="oni_lorenz")


def _buscar_lag_optimo(
    serie_a: np.ndarray,
    serie_b: np.ndarray,
    max_lag: int,
) -> int:
    """Busca el lag entre -max_lag y +max_lag que maximiza corr(shift(a, lag), b)."""
    mejor_corr = -np.inf
    mejor_lag = 0
    for lag in range(-max_lag, max_lag + 1):
        shifted = np.roll(serie_a, lag)
        corr = np.corrcoef(shifted, serie_b)[0, 1]
        if corr > mejor_corr:
            mejor_corr = corr
            mejor_lag = lag
    return mejor_lag


def generar_oni_sintetico(
    oni_filtrado: pd.Series,
    T: float = 2000.0,
    dt: float = 0.01,
    seed: int | None = 42,
) -> pd.Series:
    """Pipeline completo: integra Lorenz → normaliza → alinea al ONI real.

    Args:
        oni_filtrado: ONI real pasado por Butterworth (sirve de referencia)
        T: duración de la integración (más largo = más puntos disponibles)
        dt: paso temporal
        seed: semilla para la condición inicial. ``None`` para random.

    Returns:
        pd.Series con el ONI sintético, mismo índice que ``oni_filtrado``.

    Ejemplo:
        >>> from abm_enso.data import oni
        >>> from abm_enso.analysis.filtros import butterworth_enso
        >>> from abm_enso.analysis.lorenz import generar_oni_sintetico
        >>>
        >>> oni_real = oni.load()['oni']
        >>> oni_filt = butterworth_enso(oni_real.dropna())
        >>> oni_sint = generar_oni_sintetico(oni_filt)
        >>> oni_sint.corr(oni_filt)  # debe ser > 0.3 si la calibración fue buena
    """
    if seed is not None:
        rng = np.random.default_rng(seed)
        init = tuple(rng.uniform(-1, 1, size=3).tolist())
    else:
        init = LORENZ_INIT

    sol = integrar(T=T, dt=dt, init=init)
    x = sol[:, 0]
    return calibrar_a_oni(x, oni_filtrado)
