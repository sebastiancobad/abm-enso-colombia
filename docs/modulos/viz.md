# Módulo `viz`

Visualización interactiva tipo NetLogo con Solara.

## Arranque

```bash
abm-enso viz
```

o directamente:

```bash
solara run src/abm_enso/viz/app.py --port 8765
```

## Componentes

### `SimulacionEnVivo`

Wrapper de `ModeloCuencas` con API amigable para la UI:

```python
sim = SimulacionEnVivo(gdf_cuencas)
sim.reset_con_escenario(ParametrosSimulacion(
    escenario="historico",
    n_meses=120,
    theta=0.70,
    kappa=0.275,
))
for _ in range(120):
    sim.step()
    estado = sim.snapshot_estado()
```

### Layout

| Componente | Descripción |
|------------|-------------|
| `PanelEstado` | Dashboard superior con 4 bignums + progress bar |
| `MapaCuencas` | Choropleth matplotlib de 231 cuencas |
| `PanelSeries` | 4 subplots Plotly (ONI, activadas, humedad, SIMMA) |
| `HeatmapActivaciones` | Mapa de calor cuencas × tiempo |
| `Periodograma` | Lomb-Scargle con banda ENSO sombreada |
| `PanelControles` | Play/Pause/Step/Reset + sliders θ/κ/ruido/seed |

### Paleta

```python
COLORES_ESTADO = {
    "estiaje":  "#E8A87C",   # <25% capacidad
    "normal":   "#6D9D7C",   # 25-60%
    "humedo":   "#4A7CA8",   # 60-θ
    "saturado": "#C5352B",   # ≥θ (evento activo)
}
```

## Export

Dos formatos soportados:

### GIF (imageio)

```python
from abm_enso.viz.export import exportar_gif
path = exportar_gif(sim, params, fps=4, dpi=90)
# outputs/simulacion_historico_20260417_143022.gif
```

### MP4 (imageio-ffmpeg)

```python
from abm_enso.viz.export import exportar_mp4, ffmpeg_disponible
if ffmpeg_disponible():
    path = exportar_mp4(sim, params, fps=8, dpi=100)
```

## Limitaciones conocidas

- **Smoothness:** matplotlib re-dibuja 231 polígonos cada tick. Para animación smooth usar la opción de export y ver el GIF/MP4.
- **Primera carga:** ~15 segundos por el parsing del GeoPackage de 231 cuencas.

## API

::: abm_enso.viz
    options:
      show_root_heading: false
      show_source: false
