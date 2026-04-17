"""App Solara principal del ABM-ENSO Colombia.

Lanzamiento:
    solara run src/abm_enso/viz/app.py

O vía CLI:
    abm-enso viz

Layout:
    ┌────────────────────────────────────────────────────────┐
    │  ABM-ENSO Colombia — Modelo 1                           │
    ├──────────────┬──────────────────────────────────────────┤
    │              │         MAPA DE CUENCAS                  │
    │  CONTROLES   │      (231 polígonos coloreados)          │
    │              │                                          │
    │  Play/Pause  │                                          │
    │  Step/Reset  │                                          │
    │              │                                          │
    │  Escenario   ├──────────────────────────────────────────┤
    │  Sliders     │   Info Bar: tick, ONI, % activadas       │
    │              ├──────────────────────────────────────────┤
    │  Export      │         SERIES TEMPORALES                │
    │              │  ONI · activadas · humedad · SIMMA       │
    │              ├──────────────────────────────────────────┤
    │              │  HEATMAP       │    PERIODOGRAMA         │
    │              │  cuencas × t   │    Lomb-Scargle         │
    └──────────────┴────────────────┴──────────────────────────┘
"""

from __future__ import annotations

import threading
import time

import solara

from abm_enso.data import cuencas as cuencas_mod, oni as oni_mod
from abm_enso.viz import estado
from abm_enso.viz.controles import PanelControles, PanelEstado
from abm_enso.viz.export import exportar_gif, exportar_mp4, ffmpeg_disponible
from abm_enso.viz.heatmap import HeatmapActivaciones
from abm_enso.viz.mapa_cuencas import MapaCuencas
from abm_enso.viz.periodograma import Periodograma
from abm_enso.viz.series import PanelSeries
from abm_enso.viz.simulacion import ParametrosSimulacion, SimulacionEnVivo


# --------- Singleton lazy de datos y simulación ---------
_gdf_cuencas_cache = None
_sim_cache = None
_sim_lock = threading.Lock()


def _cargar_gdf():
    """Carga el GeoDataFrame de cuencas una sola vez (con cache)."""
    global _gdf_cuencas_cache
    if _gdf_cuencas_cache is None:
        _gdf_cuencas_cache = cuencas_mod.load()
    return _gdf_cuencas_cache


def _obtener_sim() -> SimulacionEnVivo:
    """Devuelve (o crea) la instancia única de simulación."""
    global _sim_cache
    if _sim_cache is None:
        with _sim_lock:
            if _sim_cache is None:
                _sim_cache = SimulacionEnVivo(_cargar_gdf())
    return _sim_cache


def _params_actuales() -> ParametrosSimulacion:
    """Construye ParametrosSimulacion desde el estado reactivo actual."""
    return ParametrosSimulacion(
        escenario=estado.escenario.value,
        n_meses=estado.n_meses.value,
        theta=estado.theta.value,
        kappa=estado.kappa.value,
        ruido_precip=estado.ruido.value,
        seed=estado.seed.value,
    )


# --------- Componente raíz ---------
@solara.component
def Page():
    """Ruta raíz de la app Solara."""
    sim = _obtener_sim()

    # Si aún no hay simulación activa, inicializar con defaults
    if sim.modelo is None:
        sim.reset_con_escenario(_params_actuales())

    # --------- Callbacks ---------
    def handle_reset():
        sim.reset_con_escenario(_params_actuales())
        estado.tick_actual.set(0)
        estado.jugando.set(False)

    def handle_step():
        if sim.step():
            estado.tick_actual.set(sim.tick())

    def handle_export_gif():
        estado.ultimo_export.set("⏳ Generando GIF... (esto puede tardar 30s)")
        try:
            path = exportar_gif(sim, _params_actuales())
            estado.ultimo_export.set(f"✓ GIF guardado: {path.name}")
        except Exception as e:
            estado.ultimo_export.set(f"✗ Error: {e}")

    def handle_export_mp4():
        if not ffmpeg_disponible():
            estado.ultimo_export.set("✗ ffmpeg no disponible. Instala imageio-ffmpeg.")
            return
        estado.ultimo_export.set("⏳ Generando MP4...")
        try:
            path = exportar_mp4(sim, _params_actuales())
            estado.ultimo_export.set(f"✓ MP4 guardado: {path.name}")
        except Exception as e:
            estado.ultimo_export.set(f"✗ Error: {e}")

    # --------- Autoplay loop ---------
    # Usamos use_effect con un bucle interno para avanzar mientras jugando=True
    # Nota: Solara re-ejecuta este efecto cada vez que cambia jugando o velocidad
    def _loop_autoplay():
        if not estado.jugando.value:
            return lambda: None

        stop_flag = {"stop": False}

        def correr():
            while not stop_flag["stop"] and estado.jugando.value:
                ok = sim.step()
                if not ok:
                    estado.jugando.set(False)
                    break
                estado.tick_actual.set(sim.tick())
                # Pausa según la velocidad
                time.sleep(1.0 / max(1, estado.velocidad_tps.value))

        t = threading.Thread(target=correr, daemon=True)
        t.start()

        def cleanup():
            stop_flag["stop"] = True

        return cleanup

    solara.use_effect(
        _loop_autoplay,
        dependencies=[estado.jugando.value, estado.velocidad_tps.value],
    )

    # --------- Render ---------
    # Cabecera
    with solara.AppBarTitle():
        solara.Text("ABM-ENSO Colombia · Modelo 1 — Clima/Cuencas")

    # Snapshots actuales (se recalculan en cada rerender)
    df_estado = sim.snapshot_estado()
    df_series = sim.snapshot_series()
    df_activaciones = sim.snapshot_activaciones_por_cuenca()

    # Info del tick actual
    fecha = sim.fecha_actual()
    oni_act = sim.modelo.oni_actual if sim.modelo else None
    n_activas = int(df_estado["evento"].sum()) if not df_estado.empty else 0
    n_total_agentes = len(df_estado) if not df_estado.empty else 1
    pct_act = 100.0 * n_activas / n_total_agentes if n_total_agentes else 0.0

    titulo_mapa = (
        f"t = {fecha:%Y-%m}  ·  ONI = {oni_act:+.2f}"
        if fecha and oni_act is not None else
        "Esperando inicio de simulación..."
    )

    with solara.Columns([1, 3]):
        # Columna izquierda: controles
        PanelControles(
            on_reset=handle_reset,
            on_step=handle_step,
            on_export_gif=handle_export_gif,
            on_export_mp4=handle_export_mp4,
        )

        # Columna derecha: visualización
        with solara.Column():
            # Dashboard resumen al tope
            fecha_str = f"{fecha:%Y-%m}" if fecha is not None else ""
            PanelEstado(
                tick_actual=sim.tick(),
                n_total=sim.n_meses(),
                oni_actual=oni_act,
                pct_activadas=pct_act,
                fecha_str=fecha_str,
            )

            MapaCuencas(_cargar_gdf(), df_estado, titulo=titulo_mapa)

            PanelSeries(df_series, escenario=estado.escenario.value)

            with solara.Columns([1, 1]):
                HeatmapActivaciones(df_activaciones, gdf_cuencas=_cargar_gdf())
                Periodograma(df_series)
