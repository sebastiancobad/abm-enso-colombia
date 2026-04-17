"""Panel de series temporales en Plotly.

4 subplots sincronizados verticalmente:
  1. ONI forzante (línea) con sombreado Niño/Niña
  2. % cuencas activadas (línea con fill)
  3. Humedad media (línea)
  4. Eventos SIMMA observados (opcional, si el escenario es histórico)
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import solara
from plotly.subplots import make_subplots


def _cargar_simma_mensual() -> Optional[pd.Series]:
    """Intenta cargar SIMMA y agrupar por mes. None si falla."""
    try:
        from abm_enso.data import simma as simma_mod
        df = simma_mod.load(tipo=["Deslizamiento", "Flujo"])
        mensual = (
            df.dropna(subset=["fecha_evento"])
            .set_index("fecha_evento")
            .resample("MS").size()
        )
        return mensual
    except Exception:
        return None


def dibujar_series(
    df_series: pd.DataFrame,
    escenario: str = "historico",
    incluir_simma: bool = True,
) -> go.Figure:
    """Construye la figura Plotly con los 4 paneles.

    Args:
        df_series: output de ``SimulacionEnVivo.snapshot_series()``
            con columnas oni, activaciones_pct, humedad_media.
        escenario: nombre del escenario actual (para decidir si mostrar SIMMA)
        incluir_simma: si False, no superpone SIMMA aunque el escenario sea histórico

    Returns:
        go.Figure con 4 subplots compartiendo eje X.
    """
    n_paneles = 4 if (escenario == "historico" and incluir_simma) else 3

    fig = make_subplots(
        rows=n_paneles, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=(
            "ONI forzante (°C)",
            "% cuencas activadas",
            "Humedad media (mm)",
            *(["Eventos SIMMA observados (mensual)"] if n_paneles == 4 else []),
        ),
    )

    if df_series.empty:
        fig.add_annotation(
            text="Sin datos — iniciar simulación",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#999"),
        )
        fig.update_layout(height=520, margin=dict(l=40, r=20, t=30, b=30))
        return fig

    # Panel 1: ONI con sombreado Niño/Niña
    fig.add_trace(
        go.Scatter(
            x=df_series.index, y=df_series["oni"],
            mode="lines", line=dict(color="#1A3A6B", width=1.5),
            name="ONI", showlegend=False,
            hovertemplate="%{x|%Y-%m}<br>ONI: %{y:.2f}<extra></extra>",
        ),
        row=1, col=1,
    )
    # Líneas de umbral
    for y_val, color in [(0.5, "rgba(200,50,43,0.3)"), (-0.5, "rgba(20,80,150,0.3)")]:
        fig.add_hline(y=y_val, line_dash="dot", line_color=color, row=1, col=1)
    fig.add_hline(y=0, line_color="rgba(100,100,100,0.3)", row=1, col=1)

    # Panel 2: % activadas con fill
    fig.add_trace(
        go.Scatter(
            x=df_series.index, y=df_series.get("activaciones_pct", []),
            mode="lines", fill="tozeroy",
            line=dict(color="#C5352B", width=1.5),
            fillcolor="rgba(197,53,43,0.15)",
            name="% activadas", showlegend=False,
            hovertemplate="%{x|%Y-%m}<br>%{y:.1f}%<extra></extra>",
        ),
        row=2, col=1,
    )

    # Panel 3: humedad media
    fig.add_trace(
        go.Scatter(
            x=df_series.index, y=df_series.get("humedad_media", []),
            mode="lines", line=dict(color="#0F766E", width=1.5),
            name="Humedad", showlegend=False,
            hovertemplate="%{x|%Y-%m}<br>%{y:.0f} mm<extra></extra>",
        ),
        row=3, col=1,
    )

    # Panel 4: SIMMA (solo si escenario histórico e incluir_simma)
    if n_paneles == 4:
        simma_mensual = _cargar_simma_mensual()
        if simma_mensual is not None and not df_series.empty:
            idx_comun = df_series.index.intersection(simma_mensual.index)
            if len(idx_comun) > 0:
                fig.add_trace(
                    go.Bar(
                        x=idx_comun, y=simma_mensual.loc[idx_comun],
                        marker_color="#999", opacity=0.7,
                        name="SIMMA obs", showlegend=False,
                        hovertemplate="%{x|%Y-%m}<br>%{y} eventos<extra></extra>",
                    ),
                    row=4, col=1,
                )

    fig.update_layout(
        height=520,
        margin=dict(l=40, r=20, t=30, b=30),
        showlegend=False,
        plot_bgcolor="white",
        hovermode="x unified",
    )
    # Ejes X en todos los subplots
    for i in range(1, n_paneles + 1):
        fig.update_yaxes(gridcolor="#EEE", row=i, col=1)
        fig.update_xaxes(gridcolor="#EEE", row=i, col=1)

    return fig


# --------- Componente Solara ---------
@solara.component
def PanelSeries(df_series: pd.DataFrame, escenario: str = "historico"):
    fig = dibujar_series(df_series, escenario=escenario)
    solara.FigurePlotly(fig)
