"""Exportación de la simulación como GIF animado o MP4.

Estrategia:
- Renderizamos cada tick como PNG con matplotlib.
- GIF: imageio ensambla la secuencia directamente (sin deps externas).
- MP4: usa imageio-ffmpeg si está disponible, o avisa al usuario de instalarlo.

Los exports corren en foreground (bloquean la UI) — una simulación de 120 ticks
tarda ~30 segundos. Para simulaciones largas, considerar hacer async en el
futuro.
"""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from abm_enso.utils.paths import OUTPUTS_DIR
from abm_enso.viz.mapa_cuencas import dibujar_mapa_a_buffer
from abm_enso.viz.simulacion import ParametrosSimulacion, SimulacionEnVivo


def _frames_desde_simulacion(
    sim: SimulacionEnVivo,
    params: ParametrosSimulacion,
    cada_n: int = 1,
    dpi: int = 90,
) -> list[bytes]:
    """Corre una simulación fresca desde cero y captura un PNG por tick.

    Args:
        sim: instancia de ``SimulacionEnVivo`` (se clona el GeoDataFrame)
        params: parámetros a usar (independientes del estado actual de la UI)
        cada_n: capturar un frame cada N ticks (1 = todos, 3 = ahorra memoria)
        dpi: resolución de cada frame

    Returns:
        Lista de PNG bytes.
    """
    # Reset con los params solicitados
    sim_local = SimulacionEnVivo(sim.gdf)
    sim_local.reset_con_escenario(params)

    frames: list[bytes] = []
    i = 0
    while sim_local.step():
        if i % cada_n == 0:
            fecha = sim_local.fecha_actual()
            oni = sim_local.modelo.oni_actual
            titulo = f"t = {fecha:%Y-%m}  ·  ONI = {oni:+.2f}" if fecha else ""
            estado = sim_local.snapshot_estado()
            frames.append(dibujar_mapa_a_buffer(sim.gdf, estado, titulo=titulo, dpi=dpi))
        i += 1
        if i > params.n_meses + 5:   # safety stop
            break

    return frames


def exportar_gif(
    sim: SimulacionEnVivo,
    params: ParametrosSimulacion,
    fps: int = 4,
    dpi: int = 90,
    cada_n: int = 1,
) -> Path:
    """Exporta la simulación completa como GIF animado.

    Args:
        sim: simulación (solo usa su gdf_cuencas)
        params: configuración a correr
        fps: cuadros por segundo
        dpi: resolución
        cada_n: capturar 1 de cada N ticks

    Returns:
        Path al archivo .gif escrito en ``outputs/``
    """
    import imageio.v3 as iio

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    frames_bytes = _frames_desde_simulacion(sim, params, cada_n=cada_n, dpi=dpi)
    if not frames_bytes:
        raise RuntimeError("La simulación no generó frames (params incorrectos?)")

    # Decodificar los PNG a arrays para imageio
    frames_arr = [iio.imread(b) for b in frames_bytes]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUTS_DIR / f"simulacion_{params.escenario}_{timestamp}.gif"
    iio.imwrite(out_path, frames_arr, loop=0, duration=int(1000 / fps))

    return out_path


def exportar_mp4(
    sim: SimulacionEnVivo,
    params: ParametrosSimulacion,
    fps: int = 8,
    dpi: int = 100,
    cada_n: int = 1,
) -> Path:
    """Exporta como MP4 (H.264 vía imageio-ffmpeg).

    Args:
        sim, params: ídem ``exportar_gif``
        fps: por defecto más alto que GIF (8 vs 4) porque MP4 se ve fluido
        dpi: por defecto mayor (MP4 tolera mejor la compresión)

    Returns:
        Path al archivo .mp4 en ``outputs/``.

    Raises:
        RuntimeError: si imageio-ffmpeg no está instalado.
    """
    try:
        import imageio.v3 as iio
        import imageio_ffmpeg  # noqa: F401 (solo para detectar)
    except ImportError as e:
        raise RuntimeError(
            "Export MP4 requiere imageio-ffmpeg. "
            "Instalar con: pip install imageio-ffmpeg"
        ) from e

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    frames_bytes = _frames_desde_simulacion(sim, params, cada_n=cada_n, dpi=dpi)
    if not frames_bytes:
        raise RuntimeError("La simulación no generó frames")

    frames_arr = [iio.imread(b) for b in frames_bytes]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUTS_DIR / f"simulacion_{params.escenario}_{timestamp}.mp4"
    iio.imwrite(out_path, frames_arr, fps=fps, codec="libx264")

    return out_path


def ffmpeg_disponible() -> bool:
    """True si ffmpeg está accesible (para habilitar el botón MP4)."""
    try:
        import imageio_ffmpeg
        imageio_ffmpeg.get_ffmpeg_exe()
        return True
    except (ImportError, RuntimeError):
        return shutil.which("ffmpeg") is not None
