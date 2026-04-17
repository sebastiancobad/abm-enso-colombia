"""Calibración de β₁: sensibilidad ONI → precipitación por tipo de suelo.

La ecuación central del submodelo de precipitación es:

    P_i(t) = P_{0,i}(mes) + β_{1,i} · ONI(t) + ε

Donde β_{1,i} es específico de cada cuenca i. En ausencia de datos de suelo
granulares (IGAC), agrupamos cuencas por su sensibilidad estimada y usamos
3 buckets: arcilloso (alta retención), arenoso (media), rocoso (baja).

En v0.1.0 usamos como proxy de heterogeneidad la **zona ENSO** (Andes vs
Caribe vs Pacífico vs Orinoquía) y calibramos β₁ por zona. En versiones
futuras esto se reemplaza por mapa de suelos IGAC 1:100,000.

Funciones públicas:
    ols_beta1(oni, precip_anom)         — regresión simple
    calibrar_por_grupo(df, grupos)      — calibra por cada grupo y devuelve dict
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def ols_beta1(
    oni: pd.Series,
    precip_anom: pd.Series,
) -> dict[str, float]:
    """Regresión OLS: precip_anom ~ α + β₁ · ONI + ε

    Args:
        oni: serie ONI (preferentemente filtrada)
        precip_anom: serie de anomalía de precipitación (desestacionalizada)

    Returns:
        dict con:
            - ``beta_1``: pendiente (mm/mes por °C ONI)
            - ``alpha``: intercepto
            - ``r``: correlación de Pearson
            - ``r_cuadrado``: r²
            - ``n``: número de observaciones usadas
    """
    # Alinear por índice común
    df = pd.concat([oni.rename("oni"), precip_anom.rename("precip")], axis=1).dropna()
    if len(df) < 10:
        raise ValueError(
            f"Muy pocos puntos tras alinear: {len(df)}. Mínimo 10."
        )

    x = df["oni"].values
    y = df["precip"].values

    # OLS cerrado: β = cov(x,y)/var(x), α = mean(y) - β·mean(x)
    x_centrado = x - x.mean()
    y_centrado = y - y.mean()
    beta_1 = float(np.sum(x_centrado * y_centrado) / np.sum(x_centrado ** 2))
    alpha = float(y.mean() - beta_1 * x.mean())

    r = float(np.corrcoef(x, y)[0, 1])

    return {
        "beta_1":     beta_1,
        "alpha":      alpha,
        "r":          r,
        "r_cuadrado": r ** 2,
        "n":          len(df),
    }


def calibrar_por_grupo(
    df_cuencas: pd.DataFrame,
    oni: pd.Series,
    precip_por_cuenca: pd.DataFrame,
    columna_grupo: str = "area_hidrografica",
) -> pd.DataFrame:
    """Calibra β₁ para cada grupo de cuencas (ej. área hidrográfica).

    Args:
        df_cuencas: DataFrame con al menos columnas ``id_cuenca`` y ``columna_grupo``
        oni: serie temporal ONI común a todas las cuencas
        precip_por_cuenca: DataFrame donde columnas = id_cuenca, filas = fechas
        columna_grupo: columna a usar para agrupar cuencas

    Returns:
        DataFrame con una fila por grupo y columnas:
            grupo, n_cuencas, beta_1_medio, beta_1_std, r_medio

    Ejemplo:
        >>> # 3 cuencas en 2 grupos
        >>> cuencas = pd.DataFrame({
        ...     'id_cuenca': ['A', 'B', 'C'],
        ...     'area_hidrografica': ['Andes', 'Andes', 'Caribe']
        ... })
        >>> oni = pd.Series([-1, 0, 1, -0.5, 0.5, -1, 1], name='oni')
        >>> precip = pd.DataFrame({
        ...     'A': [150, 100, 80, 130, 90, 160, 75],
        ...     'B': [140, 105, 85, 125, 92, 155, 78],
        ...     'C': [110, 100, 95, 108, 99, 115, 92],
        ... })
        >>> calibrar_por_grupo(cuencas, oni, precip)
    """
    filas = []

    for grupo, sub in df_cuencas.groupby(columna_grupo):
        betas = []
        rs = []

        for id_cuenca in sub["id_cuenca"]:
            if id_cuenca not in precip_por_cuenca.columns:
                continue
            precip_serie = precip_por_cuenca[id_cuenca].dropna()
            if len(precip_serie) < 10:
                continue

            # Desestacionalizar (anomalía mensual) si la serie tiene estacionalidad
            if isinstance(precip_serie.index, pd.DatetimeIndex):
                clim = precip_serie.groupby(precip_serie.index.month).transform("mean")
                precip_anom = precip_serie - clim
            else:
                precip_anom = precip_serie - precip_serie.mean()

            try:
                resultado = ols_beta1(oni, precip_anom)
            except ValueError:
                continue

            betas.append(resultado["beta_1"])
            rs.append(resultado["r"])

        filas.append({
            "grupo":         grupo,
            "n_cuencas":     len(betas),
            "beta_1_medio":  float(np.mean(betas)) if betas else np.nan,
            "beta_1_std":    float(np.std(betas))  if betas else np.nan,
            "r_medio":       float(np.mean(rs))    if rs else np.nan,
        })

    return pd.DataFrame(filas)
