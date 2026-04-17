"""Mapa coreopléptico de las 231 cuencas HydroBASINS coloreadas por estado.

Usa matplotlib + GeoPandas (rasterizado), se re-dibuja en cada tick.

Paletas:
- estiaje  → #D4A574 (ocre)
- normal   → #8FA68E (verde oliva)
- humedo   → #4A7CA8 (azul medio)
- saturado → #1A3A6B (azul oscuro, evento)
"""

from __future__ import annotations

import io

import matplotlib.pyplot as plt
import pandas as pd
import solara
from matplotlib import patches
from matplotlib.figure import Figure

# Paleta fija — cada estado hídrico tiene un color asociado (más contrastada)
COLORES_ESTADO = {
    "estiaje":  "#E8A87C",   # ocre más saturado
    "normal":   "#6D9D7C",   # verde más vivo
    "humedo":   "#4A7CA8",   # azul medio
    "saturado": "#C5352B",   # rojo intenso (evento activo)
}


def dibujar_mapa(
    gdf_cuencas,
    df_estado: pd.DataFrame | None = None,
    titulo: str = "",
    figsize: tuple[float, float] = (7, 7.5),
    dpi: int = 72,
) -> Figure:
    """Crea la figura del mapa coloreando cada cuenca por su estado actual.

    Args:
        gdf_cuencas: GeoDataFrame con geometría de las 231 cuencas
        df_estado: output de ``SimulacionEnVivo.snapshot_estado()``. Si es
            ``None`` o vacío, se dibuja en gris (modelo no inicializado).
        titulo: texto arriba del mapa (usualmente "t = YYYY-MM · ONI = X.X")
        figsize, dpi: tamaño y resolución
            (dpi bajo = render más rápido durante autoplay)

    Returns:
        matplotlib.Figure lista para `solara.FigureMatplotlib(fig)`
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Fondo: disolver todas las cuencas y dibujar silueta de Colombia como referencia
    try:
        contorno = gdf_cuencas.dissolve()
        contorno.boundary.plot(ax=ax, color="#333333", linewidth=0.8)
    except Exception:
        pass  # si falla, seguimos sin contorno

    # Si no hay estado, pintar todo en gris claro
    if df_estado is None or df_estado.empty:
        gdf_cuencas.plot(
            ax=ax, color="#E8E8E8", edgecolor="#AAAAAA", linewidth=0.3,
        )
        ax.set_title("Sin simulación activa — elegir escenario", fontsize=11, color="#666")
    else:
        # Merge geometría ↔ estado por id_cuenca
        gdf_con_estado = gdf_cuencas.merge(
            df_estado[["id_cuenca", "estado"]],
            on="id_cuenca",
            how="left",
        )
        gdf_con_estado["color"] = gdf_con_estado["estado"].map(COLORES_ESTADO).fillna("#DDDDDD")

        gdf_con_estado.plot(
            ax=ax,
            color=gdf_con_estado["color"],
            edgecolor="#555555",
            linewidth=0.4,
        )

        if titulo:
            ax.set_title(titulo, fontsize=12, fontweight="bold", loc="left", color="#1A3A6B")

    # Estética
    ax.set_axis_off()
    ax.set_aspect("equal")

    # Leyenda
    handles = [
        patches.Patch(color=COLORES_ESTADO["estiaje"],  label="Estiaje (<25% cap.)"),
        patches.Patch(color=COLORES_ESTADO["normal"],   label="Normal (25-60%)"),
        patches.Patch(color=COLORES_ESTADO["humedo"],   label="Húmedo (60-θ)"),
        patches.Patch(color=COLORES_ESTADO["saturado"], label="Saturado (evento)"),
    ]
    ax.legend(
        handles=handles, loc="lower left", fontsize=8, frameon=False, ncol=1,
    )

    fig.tight_layout()
    return fig


def dibujar_mapa_a_buffer(
    gdf_cuencas,
    df_estado: pd.DataFrame | None,
    titulo: str = "",
    dpi: int = 90,
) -> bytes:
    """Versión para export (GIF/MP4): retorna PNG bytes en vez de Figure."""
    fig = dibujar_mapa(gdf_cuencas, df_estado, titulo=titulo, dpi=dpi)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# --------- Componente Solara ---------
@solara.component
def MapaCuencas(gdf_cuencas, df_estado, titulo: str = ""):
    """Componente reactivo. Se re-renderiza cada vez que cambia ``df_estado``."""
    fig = dibujar_mapa(gdf_cuencas, df_estado, titulo=titulo)
    solara.FigureMatplotlib(fig, dependencies=[titulo, id(df_estado)])
