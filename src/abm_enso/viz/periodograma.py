"""Periodograma Lomb-Scargle del % de cuencas activadas.

Detecta periodicidades en la serie de activaciones. Si el modelo captura
bien el ENSO, debe aparecer un pico entre 2-7 años (0.14-0.5 ciclos/año).

Usa la función ``lomb_scargle`` de ``analysis.metricas`` (ya implementada en Fase 3).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import solara


def dibujar_periodograma(df_series: pd.DataFrame) -> go.Figure:
    """Periodograma del % activaciones a lo largo de la simulación.

    Args:
        df_series: output de snapshot_series() con 'activaciones_pct'

    Returns:
        go.Figure con periodograma y banda ENSO sombreada.
    """
    if df_series is None or df_series.empty or "activaciones_pct" not in df_series.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Sin datos — iniciar simulación",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#999"),
        )
        fig.update_layout(height=360, margin=dict(l=40, r=20, t=30, b=30))
        return fig

    from abm_enso.analysis.metricas import lomb_scargle

    serie = df_series["activaciones_pct"].dropna()
    if len(serie) < 24:
        # Muy corto para un periodograma significativo
        fig = go.Figure()
        fig.add_annotation(
            text=f"Muy pocos meses ({len(serie)}). Mínimo 24 para periodograma.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=12, color="#999"),
        )
        fig.update_layout(height=360, margin=dict(l=40, r=20, t=30, b=30))
        return fig

    freqs, power = lomb_scargle(serie, f_min_cycles_per_year=0.05, f_max_cycles_per_year=2.0)
    periodos = 1.0 / freqs  # años

    fig = go.Figure()
    # Banda ENSO sombreada (2-7 años)
    fig.add_vrect(
        x0=2, x1=7, fillcolor="rgba(30,90,175,0.1)", line_width=0,
        annotation_text="Banda ENSO (2-7 años)", annotation_position="top left",
        annotation_font=dict(size=10, color="#1A3A6B"),
    )
    fig.add_trace(go.Scatter(
        x=periodos, y=power,
        mode="lines", line=dict(color="#0F766E", width=2),
        fill="tozeroy", fillcolor="rgba(15,118,110,0.1)",
        hovertemplate="Período: %{x:.2f} años<br>Potencia: %{y:.3f}<extra></extra>",
    ))

    # Marcar el pico dominante
    idx_pico = np.argmax(power)
    fig.add_trace(go.Scatter(
        x=[periodos[idx_pico]], y=[power[idx_pico]],
        mode="markers+text",
        marker=dict(size=12, color="#C5352B", symbol="star"),
        text=[f"Pico: {periodos[idx_pico]:.2f}a"],
        textposition="top right",
        textfont=dict(size=11, color="#C5352B"),
        showlegend=False,
        hovertemplate="Pico dominante: %{x:.2f} años<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text="Periodograma Lomb-Scargle (% activaciones)",
            font=dict(size=12), x=0, xanchor="left",
        ),
        xaxis=dict(title="Período (años)", range=[0.5, 15], gridcolor="#EEE"),
        yaxis=dict(title="Potencia normalizada", gridcolor="#EEE"),
        height=360,
        margin=dict(l=60, r=20, t=40, b=40),
        plot_bgcolor="white",
        showlegend=False,
    )
    return fig


# --------- Componente Solara ---------
@solara.component
def Periodograma(df_series: pd.DataFrame):
    fig = dibujar_periodograma(df_series)
    solara.FigurePlotly(fig)
