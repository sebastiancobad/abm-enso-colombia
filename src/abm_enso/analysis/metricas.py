"""Métricas de evaluación para calibración y validación.

Todas las métricas trabajan con pd.Series o np.ndarray indistintamente.

Funciones públicas:
    pearson_r(a, b)              — correlación lineal [-1, 1]
    rmse(a, b)                   — raíz error cuadrático medio
    f1_score(y_true, y_pred)     — balance precision/recall para binarias
    lomb_scargle(serie, f_max)   — periodograma espectral
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def pearson_r(a: np.ndarray | pd.Series, b: np.ndarray | pd.Series) -> float:
    """Correlación de Pearson entre dos series.

    Args:
        a, b: series o arrays de la misma longitud

    Returns:
        float en [-1, 1]. NaN si alguna serie es constante.

    Notas:
        - Maneja NaN: los descarta par-wise.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) != len(b):
        raise ValueError(f"Longitudes distintas: {len(a)} vs {len(b)}")

    mask = ~(np.isnan(a) | np.isnan(b))
    if mask.sum() < 2:
        return np.nan

    return float(np.corrcoef(a[mask], b[mask])[0, 1])


def rmse(a: np.ndarray | pd.Series, b: np.ndarray | pd.Series) -> float:
    """Raíz del error cuadrático medio: √(mean((a-b)²))."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) != len(b):
        raise ValueError(f"Longitudes distintas: {len(a)} vs {len(b)}")
    return float(np.sqrt(np.nanmean((a - b) ** 2)))


def f1_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """F1-score para clasificación binaria.

    F1 = 2 × (precision × recall) / (precision + recall)

    Args:
        y_true: etiquetas verdaderas (0/1 o bool)
        y_pred: predicciones (0/1 o bool)

    Returns:
        F1 en [0, 1]. 0 si no hay true positives.
    """
    y_true = np.asarray(y_true, dtype=bool)
    y_pred = np.asarray(y_pred, dtype=bool)
    if len(y_true) != len(y_pred):
        raise ValueError(f"Longitudes distintas: {len(y_true)} vs {len(y_pred)}")

    tp = int(np.sum(y_true & y_pred))
    fp = int(np.sum(~y_true & y_pred))
    fn = int(np.sum(y_true & ~y_pred))

    if tp == 0:
        return 0.0

    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return float(2 * precision * recall / (precision + recall))


def lomb_scargle(
    serie: pd.Series,
    f_min_cycles_per_year: float = 0.1,
    f_max_cycles_per_year: float = 2.0,
    n_freqs: int = 500,
) -> tuple[np.ndarray, np.ndarray]:
    """Periodograma de Lomb-Scargle (funciona con series irregulares y con gaps).

    Args:
        serie: pd.Series con DatetimeIndex
        f_min_cycles_per_year, f_max_cycles_per_year: rango de frecuencias
        n_freqs: número de frecuencias a evaluar

    Returns:
        (freqs, power) — arrays de frecuencias y potencia espectral.

    Notas:
        - Útil para detectar periodicidades ENSO sin necesidad de imputar NaN
    """
    from scipy.signal import lombscargle

    if not isinstance(serie.index, pd.DatetimeIndex):
        raise TypeError("La serie debe tener DatetimeIndex")

    # Tiempo en años desde el inicio
    t_years = (serie.index - serie.index[0]).days / 365.25
    t = np.asarray(t_years, dtype=float)
    y = np.asarray(serie.values, dtype=float)

    mask = ~np.isnan(y)
    t, y = t[mask], y[mask]

    # Lomb-Scargle necesita angular frequencies (2π × f)
    freqs = np.linspace(f_min_cycles_per_year, f_max_cycles_per_year, n_freqs)
    angular = 2 * np.pi * freqs
    power = lombscargle(t, y - y.mean(), angular, normalize=True)

    return freqs, power
