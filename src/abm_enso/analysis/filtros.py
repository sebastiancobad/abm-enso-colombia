"""Filtros espectrales para aislar la señal ENSO.

El ENSO oscila con período ~2-7 años. Filtrando por esa banda eliminamos:
- Alta frecuencia: ruido intraseasonal y estacional
- Baja frecuencia: tendencia climática de largo plazo

Se usa Butterworth de orden 4 con `filtfilt` (fase cero, no introduce desfase).

Funciones públicas:
    butterworth_enso(serie)         — filtro pasa-banda 2-7 años
    desestacionalizar(serie)        — resta la climatología mensual
    filtrar_fuente(serie, ...)      — pipeline completo (deestacionaliza + filtra)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

from abm_enso.utils.constants import (
    BUTTERWORTH_HIGH_CYCLES_PER_YEAR,
    BUTTERWORTH_LOW_CYCLES_PER_YEAR,
    BUTTERWORTH_ORDER,
)


def butterworth_enso(
    serie: pd.Series,
    fs_cycles_per_year: float = 12.0,
    low: float = BUTTERWORTH_LOW_CYCLES_PER_YEAR,
    high: float = BUTTERWORTH_HIGH_CYCLES_PER_YEAR,
    order: int = BUTTERWORTH_ORDER,
) -> pd.Series:
    """Aplica Butterworth pasa-banda 2-7 años (señal ENSO).

    Args:
        serie: serie mensual regular (sin huecos), indexada por fecha
        fs_cycles_per_year: frecuencia de muestreo en ciclos/año
            (12 = mensual, 365 = diario)
        low: frecuencia de corte baja (ciclos/año) — default 1/7 ≈ 0.143
        high: frecuencia de corte alta — default 1/2 = 0.5
        order: orden del filtro — default 4

    Returns:
        Serie filtrada con el mismo índice que la entrada.

    Raises:
        ValueError: si la serie tiene NaN (usar `interpolate()` antes)
        ValueError: si la serie es muy corta (< 3 × orden)

    Notas:
        - Se usa `filtfilt` para fase cero (el filtro no desplaza la señal).
        - Las frecuencias se normalizan al Nyquist (fs/2) internamente.
    """
    if serie.isna().any():
        raise ValueError(
            f"Serie contiene {serie.isna().sum()} NaN. Usa `.interpolate()` antes."
        )
    if len(serie) < 3 * order:
        raise ValueError(
            f"Serie muy corta ({len(serie)} puntos) para orden {order}. "
            f"Mínimo: {3 * order}"
        )

    nyquist = fs_cycles_per_year / 2
    low_norm = low / nyquist
    high_norm = high / nyquist

    # Sanity: frecuencias deben estar en (0, 1)
    if not (0 < low_norm < high_norm < 1):
        raise ValueError(
            f"Frecuencias fuera de rango. low={low_norm:.3f}, high={high_norm:.3f}. "
            f"Deben cumplir 0 < low < high < 1 tras normalizar por Nyquist."
        )

    b, a = butter(order, [low_norm, high_norm], btype="band")
    filtrada = filtfilt(b, a, serie.values)
    return pd.Series(filtrada, index=serie.index, name=f"{serie.name}_enso")


def desestacionalizar(serie: pd.Series) -> pd.Series:
    """Resta la climatología mensual (promedio por mes calendario).

    Convierte una serie mensual con ciclo estacional en una serie de anomalías
    mensuales respecto a la climatología de todo el período.

    Args:
        serie: pd.Series con DatetimeIndex mensual

    Returns:
        Serie de anomalías con el mismo índice.

    Ejemplo:
        >>> precip = pd.Series([100, 200, 150, 100, 200, 150],
        ...                    index=pd.date_range('2020-01', periods=6, freq='MS'))
        >>> anom = desestacionalizar(precip)
        >>> anom.tolist()  # cada valor - su climatología mensual
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    """
    if not isinstance(serie.index, pd.DatetimeIndex):
        raise TypeError("La serie debe tener DatetimeIndex")

    climatologia = serie.groupby(serie.index.month).transform("mean")
    anomalia = serie - climatologia
    anomalia.name = f"{serie.name}_anom" if serie.name else "anomalia"
    return anomalia


def filtrar_fuente(
    serie: pd.Series,
    quitar_clima: bool = True,
    interpolar_gaps: bool = True,
) -> pd.Series:
    """Pipeline completo: desestacionaliza (opcional) + interpola gaps + Butterworth.

    Args:
        serie: serie mensual cruda (puede tener huecos)
        quitar_clima: si ``True``, resta climatología mensual antes del filtro.
            Para ONI es ``False`` (ya es anomalía). Para ERA5/SIMMA/SIRH es ``True``.
        interpolar_gaps: rellena NaN por interpolación lineal antes del filtro

    Returns:
        Serie filtrada en la banda ENSO.
    """
    s = serie.copy()

    if quitar_clima:
        s = desestacionalizar(s)

    if interpolar_gaps and s.isna().any():
        s = s.interpolate(method="linear", limit_direction="both")

    return butterworth_enso(s)
