"""Panel de controles tipo NetLogo: play/pause/step, sliders, selector escenario.

Incluye un dashboard (PanelEstado) con tick / fecha / ONI / % activadas
y una barra de progreso para dar contexto inmediato al usuario.
"""

from __future__ import annotations

import solara

from abm_enso.viz import estado


def _fase_enso(oni_value: float | None) -> tuple[str, str]:
    """Devuelve (etiqueta, color) de la fase ENSO según umbral ± 0.5."""
    if oni_value is None:
        return ("—", "#888")
    if oni_value >= 0.5:
        return ("El Niño", "#C5352B")
    if oni_value <= -0.5:
        return ("La Niña", "#1A3A6B")
    return ("Neutro", "#6D9D7C")


@solara.component
def PanelEstado(
    tick_actual: int,
    n_total: int,
    oni_actual: float | None,
    pct_activadas: float | None,
    fecha_str: str = "",
):
    """Dashboard superior con 4 métricas grandes + barra de progreso."""
    fase_lbl, fase_color = _fase_enso(oni_actual)
    pct = pct_activadas if pct_activadas is not None else 0.0
    progreso = 100 * tick_actual / max(1, n_total)

    with solara.Card(style={
        "background": "#F8F9FB",
        "border-left": "6px solid #1A3A6B",
        "padding": "12px 16px",
        "margin-bottom": "12px",
    }):
        solara.ProgressLinear(value=progreso, color="primary")

        with solara.Row(style={"margin-top": "10px", "gap": "24px"}):
            with solara.Column(align="center", style={"flex": 1}):
                solara.Markdown(f"**Tick**\n\n### {tick_actual} / {n_total}")

            with solara.Column(align="center", style={"flex": 1}):
                solara.Markdown(f"**Fecha**\n\n### {fecha_str or '—'}")

            with solara.Column(align="center", style={"flex": 1}):
                oni_txt = f"{oni_actual:+.2f}" if oni_actual is not None else "—"
                solara.Markdown(f"**ONI**\n\n### {oni_txt}")
                solara.Markdown(
                    f"<span style='color:{fase_color}; font-weight:bold'>{fase_lbl}</span>",
                )

            with solara.Column(align="center", style={"flex": 1}):
                pct_color = "#C5352B" if pct > 40 else "#1A3A6B" if pct > 15 else "#6D9D7C"
                solara.Markdown(
                    f"**% activadas**\n\n### <span style='color:{pct_color}'>{pct:.1f}%</span>",
                )


@solara.component
def PanelControles(
    on_reset,
    on_step,
    on_export_gif,
    on_export_mp4,
):
    """Panel lateral con todos los controles del simulador."""
    with solara.Card("Controles", style={"min-width": "300px", "max-width": "340px"}):

        with solara.Row():
            if estado.jugando.value:
                solara.Button(
                    "⏸ Pause", color="warning",
                    on_click=lambda: estado.jugando.set(False),
                )
            else:
                solara.Button(
                    "▶ Play", color="primary",
                    on_click=lambda: estado.jugando.set(True),
                )
            solara.Button(
                "⏭ Step", on_click=on_step,
                disabled=estado.jugando.value,
            )
            solara.Button(
                "↻ Reset", color="secondary",
                on_click=on_reset,
            )

        solara.Info(
            "Velocidad baja = más fluido. Tras cambiar sliders, pulsa Reset.",
            dense=True, icon=False,
        )

        solara.SliderInt(
            label=f"⚡ Velocidad: {estado.velocidad_tps.value} ticks/seg",
            value=estado.velocidad_tps,
            min=1, max=10, step=1,
        )

        solara.Markdown("---")

        solara.Markdown("### 🌊 Escenario ENSO")
        etiquetas = {k: v for k, v in estado.OPCIONES_ESCENARIO}
        solara.Select(
            label="",
            value=estado.escenario,
            values=[k for k, _ in estado.OPCIONES_ESCENARIO],
        )
        solara.Text(
            etiquetas.get(estado.escenario.value, ""),
            style={"font-size": "0.82em", "color": "#666", "margin-top": "-6px"},
        )

        solara.SliderInt(
            label=f"📅 Meses: {estado.n_meses.value}",
            value=estado.n_meses,
            min=12, max=240, step=12,
        )

        solara.Markdown("---")

        solara.Markdown("### ⚙️ Parámetros del modelo")
        solara.SliderFloat(
            label=f"θ (umbral activación): {estado.theta.value:.3f}",
            value=estado.theta,
            min=0.50, max=0.95, step=0.025,
        )
        solara.SliderFloat(
            label=f"κ (drenaje mensual): {estado.kappa.value:.3f}",
            value=estado.kappa,
            min=0.05, max=0.50, step=0.025,
        )
        solara.SliderFloat(
            label=f"ε (ruido estocástico): {estado.ruido.value:.1f} mm",
            value=estado.ruido,
            min=0.0, max=30.0, step=2.5,
        )
        solara.SliderInt(
            label=f"🎲 Seed: {estado.seed.value}",
            value=estado.seed,
            min=1, max=1000, step=1,
        )

        solara.Markdown("---")

        solara.Markdown("### 💾 Exportar simulación")
        with solara.Row():
            solara.Button("🎞 GIF", on_click=on_export_gif)
            solara.Button("🎬 MP4", on_click=on_export_mp4)

        if estado.ultimo_export.value:
            if estado.ultimo_export.value.startswith("✓"):
                solara.Success(estado.ultimo_export.value, dense=True)
            elif estado.ultimo_export.value.startswith("✗"):
                solara.Error(estado.ultimo_export.value, dense=True)
            else:
                solara.Info(estado.ultimo_export.value, dense=True)


# Backwards-compat
@solara.component
def InfoBar(tick_actual: int, n_total: int, oni_actual: float | None, pct_activadas: float | None):
    """[DEPRECATED] Usar PanelEstado."""
    PanelEstado(tick_actual, n_total, oni_actual, pct_activadas, fecha_str="")
