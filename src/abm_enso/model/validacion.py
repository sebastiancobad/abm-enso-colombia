"""Validación del ABM contra eventos SIMMA observados.

Para el período 2010-2012 (La Niña), comparamos:
    - Activaciones simuladas agregadas a mensual
    - Eventos SIMMA reales filtrados por tipo y alcance temporal

Métricas:
    Pearson r, RMSE, F1-score entre ambas series de conteo.

Uso:
    >>> from abm_enso.model import validacion
    >>> r, rmse_val, f1 = validacion.validar_contra_simma(modelo, "2010-01", "2012-12")
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from abm_enso.analysis.metricas import f1_score, pearson_r, rmse


def agregar_activaciones_mensual(modelo) -> pd.Series:
    """Agrega las activaciones de todas las cuencas a conteo mensual.

    Returns:
        Serie indexada por fecha con el número de cuencas activas por mes.
    """
    df = modelo.resumen_temporal()
    if df.empty:
        return pd.Series(dtype=int, name="n_activaciones_sim")
    return df.set_index("fecha")["n_activaciones"].rename("n_activaciones_sim")


def obtener_simma_mensual(
    inicio: str = "2010-01",
    fin: str = "2012-12",
    tipos: list[str] | None = None,
) -> pd.Series:
    """Carga SIMMA y lo agrega a conteo mensual en el rango dado."""
    from abm_enso.data import simma as simma_mod

    tipos = tipos or ["Deslizamiento", "Flujo"]
    df = simma_mod.load(tipo=tipos)

    if "fecha_evento" not in df.columns:
        raise ValueError("SIMMA cargado sin columna 'fecha_evento'")

    df = df.dropna(subset=["fecha_evento"])
    df["fecha_evento"] = pd.to_datetime(df["fecha_evento"], errors="coerce")
    df = df.dropna(subset=["fecha_evento"])

    # Filtrar al rango
    mask = (df["fecha_evento"] >= inicio) & (df["fecha_evento"] <= fin)
    sub = df.loc[mask].set_index("fecha_evento")

    return sub.resample("MS").size().rename("n_eventos_simma")


def validar_contra_simma(
    modelo,
    inicio: str = "2010-01",
    fin: str = "2012-12",
    umbral_sim: int = 50,
    umbral_obs: int = 5,
) -> dict:
    """Calcula métricas de ajuste entre activaciones simuladas y eventos SIMMA.

    Args:
        modelo: ``ModeloCuencas`` que ya corrió ``.run()``
        inicio, fin: rango temporal de validación
        umbral_sim: mínimo de cuencas activas para considerar 'evento binario'
        umbral_obs: mínimo de reportes SIMMA para considerar 'evento binario'

    Returns:
        dict con 'r', 'rmse', 'f1', 'n_meses', 'serie_sim', 'serie_obs'.
    """
    sim = agregar_activaciones_mensual(modelo).loc[inicio:fin]
    obs = obtener_simma_mensual(inicio=inicio, fin=fin)

    # Alinear índices (mensualmente)
    idx = sim.index.intersection(obs.index)
    if len(idx) < 3:
        return {
            "r":          np.nan,
            "rmse":       np.nan,
            "f1":         np.nan,
            "n_meses":    len(idx),
            "serie_sim":  sim,
            "serie_obs":  obs,
            "warning":    f"Pocos meses alineados ({len(idx)})",
        }

    sim_a = sim.loc[idx].values
    obs_a = obs.loc[idx].values

    # Binarizar ambas con sus umbrales respectivos
    sim_bin = sim_a > umbral_sim
    obs_bin = obs_a > umbral_obs

    return {
        "r":          pearson_r(sim_a, obs_a),
        "rmse":       rmse(sim_a, obs_a),
        "f1":         f1_score(obs_bin, sim_bin),
        "n_meses":    len(idx),
        "serie_sim":  sim.loc[idx],
        "serie_obs":  obs.loc[idx],
    }
