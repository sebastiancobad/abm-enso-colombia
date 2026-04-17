"""Calibración conjunta de θ (umbral de evento) y κ (tasa de drenaje).

Ecuaciones del submodelo hidrológico:

    Balance:   H(t+1) = (1 - κ) · H(t) + P(t+1)
    Evento:    E(t)   = 1{ H(t) > θ · C }

Donde:
    H(t) : humedad acumulada en la cuenca en el tick t [mm]
    P(t) : precipitación del mes [mm]
    C    : capacidad hídrica de la cuenca [mm]
    θ    : fracción de C que activa riesgo [0, 1]
    κ    : tasa de drenaje mensual [0, 1]

La calibración busca el par (θ*, κ*) que maximiza el F1-score entre:
    - E(t) simulado por la cuenca (dado precipitación real)
    - Eventos observados en SIMMA agregados a mensual

Usa grid search en el rango ``θ ∈ [0.60, 0.95]`` y ``κ ∈ [0.05, 0.45]``.

Funciones públicas:
    simular_eventos(precip, theta, kappa, capacidad)   — simulación escalar
    grid_search_f1(precip, eventos_obs, theta_grid, kappa_grid)
    calibrar(precip, eventos_obs)                       — pipeline con defaults
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from abm_enso.analysis.metricas import f1_score


@dataclass
class ResultadoCalibracion:
    """Output del grid search."""
    theta_opt: float
    kappa_opt: float
    f1_opt: float
    grid: pd.DataFrame            # DataFrame con columnas theta, kappa, f1
    theta_grid: np.ndarray
    kappa_grid: np.ndarray
    f1_matrix: np.ndarray         # shape (len(theta_grid), len(kappa_grid))


def simular_eventos(
    precip: np.ndarray,
    theta: float,
    kappa: float,
    capacidad: float = 1000.0,
    humedad_inicial: float = 0.0,
) -> np.ndarray:
    """Simula la dinámica de humedad y los eventos de una cuenca.

    Args:
        precip: array 1D de precipitación mensual [mm]
        theta: umbral de activación (fracción de capacidad)
        kappa: tasa de drenaje mensual
        capacidad: capacidad hídrica máxima [mm]
        humedad_inicial: H(0) [mm]

    Returns:
        Array 1D booleano del mismo largo que ``precip``: True si hay evento.
    """
    h = humedad_inicial
    eventos = np.zeros(len(precip), dtype=bool)
    umbral = theta * capacidad

    for t in range(len(precip)):
        h = (1 - kappa) * h + precip[t]
        h = max(h, 0.0)  # clip inferior
        eventos[t] = h > umbral

    return eventos


def grid_search_f1(
    precip: np.ndarray | pd.Series,
    eventos_obs: np.ndarray | pd.Series,
    theta_grid: Iterable[float] | None = None,
    kappa_grid: Iterable[float] | None = None,
    capacidad: float = 1000.0,
) -> ResultadoCalibracion:
    """Grid search para (θ, κ) maximizando F1 contra eventos observados.

    Args:
        precip: serie mensual de precipitación
        eventos_obs: serie binaria de eventos observados (mismo largo y alineada)
        theta_grid: iterable de θ candidatos. Default: [0.60, 0.95] paso 0.025
        kappa_grid: iterable de κ candidatos. Default: [0.05, 0.45] paso 0.025
        capacidad: capacidad hídrica de referencia [mm]

    Returns:
        ResultadoCalibracion con θ*, κ*, F1 óptimo y la grilla completa.
    """
    precip_arr = np.asarray(precip, dtype=float)
    eventos_arr = np.asarray(eventos_obs, dtype=bool)

    if len(precip_arr) != len(eventos_arr):
        raise ValueError(
            f"precip ({len(precip_arr)}) y eventos_obs ({len(eventos_arr)}) "
            f"deben tener la misma longitud."
        )

    if theta_grid is None:
        theta_grid = np.arange(0.60, 0.96, 0.025)
    if kappa_grid is None:
        kappa_grid = np.arange(0.05, 0.46, 0.025)

    theta_arr = np.asarray(list(theta_grid))
    kappa_arr = np.asarray(list(kappa_grid))

    f1_matrix = np.zeros((len(theta_arr), len(kappa_arr)))
    filas = []

    for i, theta in enumerate(theta_arr):
        for j, kappa in enumerate(kappa_arr):
            eventos_sim = simular_eventos(
                precip_arr, theta=theta, kappa=kappa, capacidad=capacidad
            )
            f1 = f1_score(eventos_arr, eventos_sim)
            f1_matrix[i, j] = f1
            filas.append({"theta": theta, "kappa": kappa, "f1": f1})

    df_grid = pd.DataFrame(filas)
    idx_opt = np.unravel_index(np.argmax(f1_matrix), f1_matrix.shape)
    theta_opt = float(theta_arr[idx_opt[0]])
    kappa_opt = float(kappa_arr[idx_opt[1]])
    f1_opt = float(f1_matrix[idx_opt])

    return ResultadoCalibracion(
        theta_opt=theta_opt,
        kappa_opt=kappa_opt,
        f1_opt=f1_opt,
        grid=df_grid,
        theta_grid=theta_arr,
        kappa_grid=kappa_arr,
        f1_matrix=f1_matrix,
    )


def calibrar(
    precip: pd.Series,
    eventos_obs: pd.Series,
    capacidad: float = 1000.0,
) -> ResultadoCalibracion:
    """Wrapper con defaults sensatos para el flujo típico.

    Args:
        precip: serie mensual de precipitación
        eventos_obs: serie binaria del mismo índice con 1 si hay evento SIMMA
        capacidad: capacidad hídrica [mm]

    Returns:
        ResultadoCalibracion
    """
    return grid_search_f1(
        precip=precip, eventos_obs=eventos_obs, capacidad=capacidad
    )
