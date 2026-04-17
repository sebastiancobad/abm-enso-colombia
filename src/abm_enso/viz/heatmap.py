"""Heatmap Plotly de activaciones por cuenca (filas) × tiempo (columnas).

Muestra patrones espacio-temporales: permite ver si ciertas cuencas siempre
se activan juntas durante eventos ENSO, y cómo el estrés se propaga.

Las cuencas se ordenan por área hidrográfica para que los patrones por región
sean visualmente evidentes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import solara


def dibujar_heatmap(
    df_activaciones: pd.DataFrame,
    gdf_cuencas=None,
    max_cuencas: int = 80,
) -> go.Figure:
    """Heatmap binario de activaciones.

    Args:
        df_activaciones: DataFrame con una fila por cuenca y columnas
            ``id_cuenca``, ``n_eventos``, ``fechas_eventos`` (lista de Timestamps).
            Output de ``ModeloCuencas.activaciones_por_cuenca()``.
        gdf_cuencas: GeoDataFrame de cuencas (para ordenar por área)
        max_cuencas: muestra solo las N con más eventos

    Returns:
        go.Figure heatmap.
    """
    if df_activaciones is None or df_activaciones.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Sin datos — iniciar simulación",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#999"),
        )
        fig.update_layout(height=360, margin=dict(l=40, r=20, t=30, b=30))
        return fig

    # Seleccionar las max_cuencas con más activaciones (si hay alguna)
    if "n_eventos" not in df_activaciones.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Sin eventos aún — avanzar simulación",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#999"),
        )
        fig.update_layout(height=360, margin=dict(l=40, r=20, t=30, b=30))
        return fig

    df_top = df_activaciones.nlargest(max_cuencas, "n_eventos").copy()

    # Ordenar por área hidrográfica si está disponible
    if "area_hidrografica" in df_top.columns:
        df_top = df_top.sort_values(["area_hidrografica", "n_eventos"], ascending=[True, False])

    # Reconstruir matriz binaria cuenca × tiempo a partir de fechas_eventos (listas)
    todas_las_fechas = set()
    for fechas in df_top["fechas_eventos"]:
        if isinstance(fechas, (list, tuple)):
            todas_las_fechas.update(fechas)

    if not todas_las_fechas:
        fig = go.Figure()
        fig.add_annotation(
            text="Sin activaciones aún — dejar correr la simulación",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#999"),
        )
        fig.update_layout(height=360, margin=dict(l=40, r=20, t=30, b=30))
        return fig

    fechas_ordenadas = sorted(todas_las_fechas)
    # Construir matriz (cuencas en filas, tiempo en columnas)
    ids = df_top["id_cuenca"].tolist()
    mat = pd.DataFrame(
        0, index=ids, columns=fechas_ordenadas, dtype=float,
    )
    for _, row in df_top.iterrows():
        fechas_evento = row["fechas_eventos"]
        if isinstance(fechas_evento, (list, tuple)):
            for f in fechas_evento:
                if f in mat.columns:
                    mat.loc[row["id_cuenca"], f] = 1.0

    fig = go.Figure(data=go.Heatmap(
        z=mat.values,
        x=[f"t={f}" for f in fechas_ordenadas],
        y=[str(c)[-10:] for c in ids],
        colorscale=[[0, "#F5F5F5"], [0.5, "#EBA28D"], [1, "#C5352B"]],
        showscale=False,
        hovertemplate="Cuenca: %{y}<br>Tick: %{x}<br>Evento: %{z:.0f}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(
            text=f"Activaciones por cuenca × tiempo (top {min(max_cuencas, len(ids))})",
            font=dict(size=12), x=0, xanchor="left",
        ),
        height=360,
        margin=dict(l=80, r=20, t=40, b=30),
        plot_bgcolor="white",
    )
    fig.update_yaxes(tickfont=dict(size=7), autorange="reversed")
    fig.update_xaxes(gridcolor="#EEE", tickfont=dict(size=8))
    return fig


# --------- Componente Solara ---------
@solara.component
def HeatmapActivaciones(df_activaciones, gdf_cuencas=None):
    fig = dibujar_heatmap(df_activaciones, gdf_cuencas=gdf_cuencas)
    solara.FigurePlotly(fig)
