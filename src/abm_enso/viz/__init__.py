"""Subpaquete `viz`: visualización interactiva tipo NetLogo con Solara.

Lanzamiento de la app:
    solara run src/abm_enso/viz/app.py

O vía CLI:
    abm-enso viz

Módulos públicos:
    app             — layout y ruta raíz Solara
    simulacion      — wrapper de ModeloCuencas para la UI
    estado          — variables reactivas compartidas
    mapa_cuencas    — choropleth de las 231 cuencas (matplotlib)
    series          — panel de series temporales (Plotly, 4 subplots)
    heatmap         — mapa de calor cuencas × tiempo (Plotly)
    periodograma    — Lomb-Scargle con banda ENSO sombreada (Plotly)
    controles       — panel lateral tipo NetLogo
    export          — GIF / MP4
"""

from abm_enso.viz.simulacion import SimulacionEnVivo, ParametrosSimulacion

__all__ = ["SimulacionEnVivo", "ParametrosSimulacion"]
