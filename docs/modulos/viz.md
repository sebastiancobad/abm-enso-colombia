# Módulo `viz`

> **Estado:** pendiente de implementación en [Fase 5](../roadmap.md#fase-5--visualización-solara-tipo-netlogo).

Este subpaquete implementa la visualización interactiva tipo NetLogo usando Solara.

## Estructura prevista

```
src/abm_enso/viz/
├── __init__.py
├── app.py            # Componente Solara principal
├── mapa_cuencas.py   # Renderizador espacial (GeoPandas + Matplotlib)
├── series.py         # Paneles temporales (Plotly)
└── export.py         # Export a GIF / MP4 con Pillow / imageio
```

## Ejecución

```bash
solara run src/abm_enso/viz/app.py
```

O directamente:

```bash
abm-enso viz
```

## Componentes de la UI

### Panel izquierdo — controles

- **Play / Pause / Step / Reset** — controles del tick
- **Velocidad** — ticks por segundo (1× a 20×)
- **Escenario** — `nina-2010` · `nino-2015` · `neutro` · `custom`
- **Sliders de parámetros** — $\theta \in [0.60, 0.95]$, $\kappa \in [0.05, 0.40]$, $\beta_1^{\text{arcilloso}}$, $\beta_1^{\text{arenoso}}$, $\beta_1^{\text{rocoso}}$
- **Botón Export GIF**

### Panel central — mapa

- Colombia con las ~316 cuencas IDEAM
- Cada cuenca pintada según su `estado`:

| Estado | Color | Hex |
|---|---|---|
| estiaje | naranja-marrón | `#B45309` |
| normal | gris claro | `#D1D5DB` |
| húmedo | azul medio | `#60A5FA` |
| saturado | rojo | `#DC2626` |

- Cuencas con evento activo (`E=1`) resaltadas con borde negro
- Contador de activaciones y fecha actual arriba del mapa

### Panel derecho — series temporales

- Panel 1: ONI con umbrales ±0.5°C
- Panel 2: humedad media global
- Panel 3: número de activaciones por tick
- Todos sincronizados con el tick actual (línea vertical móvil)

## Ejemplo de estructura Solara

```python
import solara
from abm_enso.model import ModeloCuencas

tick = solara.reactive(0)
theta = solara.reactive(0.78)
kappa = solara.reactive(0.22)
playing = solara.reactive(False)

@solara.component
def Page():
    with solara.AppBar():
        solara.AppBarTitle("ABM-ENSO-Colombia")

    with solara.Sidebar():
        solara.SliderFloat("θ (umbral)", value=theta, min=0.60, max=0.95)
        solara.SliderFloat("κ (drenaje)", value=kappa, min=0.05, max=0.40)
        solara.Button("▶ Play" if not playing.value else "⏸ Pause",
                      on_click=lambda: playing.set(not playing.value))

    with solara.Columns([3, 2]):
        MapaCuencas(tick=tick.value, theta=theta.value, kappa=kappa.value)
        with solara.Column():
            PanelONI(tick=tick.value)
            PanelHumedad(tick=tick.value)
            PanelActivaciones(tick=tick.value)
```

## Export a GIF

```python
from abm_enso.viz import export

export.corrida_a_gif(
    modelo=modelo,
    output_path="outputs/simulations/nina_2010.gif",
    fps=4,
    incluir_series=True,
)
```
