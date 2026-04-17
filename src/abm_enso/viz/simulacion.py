"""Wrapper del ABM para uso desde la UI Solara.

Provee una API simplificada:
- ``SimulacionEnVivo`` mantiene un ``ModeloCuencas`` y su historial
- métodos ``reset_con_escenario``, ``step``, ``run_hasta``
- snapshots para renderizado (estado por cuenca, series temporales agregadas)

La UI nunca toca ``ModeloCuencas`` directamente, solo ``SimulacionEnVivo``.
Esto centraliza la gestión de estado y simplifica el testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from abm_enso.model import (
    BETA1_POR_AREA_DEFAULT,
    ModeloCuencas,
    escenarios,
    validacion,
)


@dataclass
class ParametrosSimulacion:
    """Hiperparámetros que controla la UI."""
    escenario: str = "historico"
    n_meses: int = 120
    theta: float = 0.78
    kappa: float = 0.22
    ruido_precip: float = 0.0
    seed: int = 42
    beta1_por_area: dict[str, float] = field(default_factory=lambda: dict(BETA1_POR_AREA_DEFAULT))


class SimulacionEnVivo:
    """Orquestador de una simulación interactiva.

    Uso típico:
        sim = SimulacionEnVivo(gdf_cuencas)
        sim.reset_con_escenario(ParametrosSimulacion(escenario="nina-2010"))
        for _ in range(120):
            sim.step()
            snap = sim.snapshot_estado()  # renderizar en UI
    """

    def __init__(self, gdf_cuencas: "pd.DataFrame | object"):
        """
        Args:
            gdf_cuencas: GeoDataFrame con las cuencas (debe tener geometry,
                id_cuenca, area_hidrografica). Suele venir de
                ``abm_enso.data.cuencas.load()``.
        """
        self.gdf = gdf_cuencas
        self.modelo: ModeloCuencas | None = None
        self.params = ParametrosSimulacion()
        self._oni_serie: pd.Series | None = None

    # ----------------------------------------------------------------
    # Reset y construcción
    # ----------------------------------------------------------------
    def reset_con_escenario(self, params: ParametrosSimulacion) -> None:
        """Reinicia el modelo con nuevos parámetros."""
        self.params = params
        self._oni_serie = self._resolver_oni_serie(params)

        self.modelo = ModeloCuencas(
            gdf_cuencas=self.gdf,
            oni_serie=self._oni_serie,
            beta1_por_area=params.beta1_por_area,
            theta=params.theta,
            kappa=params.kappa,
            ruido_precip=params.ruido_precip,
            seed=params.seed,
        )

    def _resolver_oni_serie(self, params: ParametrosSimulacion) -> pd.Series:
        """Obtiene la serie ONI según el escenario elegido.

        Nota: los escenarios tienen firmas distintas:
        - nina_2010, nino_2015, neutro, lorenz: aceptan n_meses
        - historico: usa rango inicio/fin
        """
        nombre = params.escenario.lower()
        if nombre == "historico":
            # Calcular fin desde inicio y n_meses (default: 2010-01-01 + n_meses)
            inicio = pd.Timestamp("2010-01-01")
            fin = inicio + pd.DateOffset(months=params.n_meses - 1)
            serie = escenarios.escenario_historico(
                inicio=inicio.strftime("%Y-%m-%d"),
                fin=fin.strftime("%Y-%m-%d"),
            )
            # Si hay menos meses de los pedidos (ej. faltan datos), ajustar
            if serie.empty:
                raise ValueError(
                    "Histórico vacío. Verifica que data/raw/oni_mensual.csv exista."
                )
            return serie
        elif nombre == "nina-2010":
            return escenarios.escenario_nina_2010(n_meses=params.n_meses)
        elif nombre == "nino-2015":
            return escenarios.escenario_nino_2015(n_meses=params.n_meses)
        elif nombre == "neutro":
            return escenarios.escenario_neutro(n_meses=params.n_meses, seed=params.seed)
        elif nombre == "lorenz":
            return escenarios.escenario_lorenz(n_meses=params.n_meses, seed=params.seed)
        else:
            raise ValueError(f"Escenario desconocido: {nombre}")

    # ----------------------------------------------------------------
    # Ejecución tick a tick
    # ----------------------------------------------------------------
    def step(self) -> bool:
        """Avanza un mes. Retorna False si el forzamiento ya se acabó."""
        if self.modelo is None:
            raise RuntimeError("Llamar reset_con_escenario antes de step.")
        if self.modelo.tick >= len(self._oni_serie):
            return False
        self.modelo.step()
        return True

    def run_hasta(self, tick: int) -> None:
        """Avanza hasta el tick indicado."""
        if self.modelo is None:
            raise RuntimeError("Llamar reset_con_escenario antes de run.")
        while self.modelo.tick < tick and self.step():
            pass

    def tick(self) -> int:
        return self.modelo.tick if self.modelo else 0

    def n_meses(self) -> int:
        return len(self._oni_serie) if self._oni_serie is not None else 0

    def fecha_actual(self) -> pd.Timestamp | None:
        """Devuelve la fecha del tick actual (o None si no empezó)."""
        if self.modelo is None or self.modelo.tick == 0:
            return None
        idx = self.modelo.tick - 1
        return self._oni_serie.index[idx]

    # ----------------------------------------------------------------
    # Snapshots para render
    # ----------------------------------------------------------------
    def snapshot_estado(self) -> pd.DataFrame:
        """Estado hídrico actual de cada cuenca.

        Returns:
            DataFrame con columnas: id_cuenca, humedad, capacidad_hidrica,
            frac_humedad, estado (estiaje/normal/humedo/saturado), evento.
        """
        if self.modelo is None:
            return pd.DataFrame()
        return self.modelo.estado_actual_por_cuenca()

    def snapshot_series(self) -> pd.DataFrame:
        """Series temporales agregadas hasta el tick actual.

        Returns:
            DataFrame indexado por fecha con:
            - oni: forzamiento aplicado
            - activaciones_pct: % cuencas con evento en ese tick
            - humedad_media: humedad promedio (mm)
        """
        if self.modelo is None or self.modelo.tick == 0:
            return pd.DataFrame(columns=["oni", "activaciones_pct", "humedad_media"])

        df = self.modelo.resumen_temporal()
        if df.empty:
            return pd.DataFrame(columns=["oni", "activaciones_pct", "humedad_media"])

        # resumen_temporal() retorna columnas: tick, fecha, oni, n_activaciones, humedad_media
        # Convertir a índice fecha y renombrar para la UI
        df = df.set_index("fecha")

        # Convertir n_activaciones absolutas a %
        n_agentes = len(list(self.modelo.agents))
        if n_agentes > 0:
            df["activaciones_pct"] = 100.0 * df["n_activaciones"] / n_agentes
        else:
            df["activaciones_pct"] = 0.0

        return df[["oni", "activaciones_pct", "humedad_media"]]

    def snapshot_activaciones_por_cuenca(self) -> pd.DataFrame:
        """Matriz de activaciones (cuenca × tiempo) para el heatmap."""
        if self.modelo is None or self.modelo.tick == 0:
            return pd.DataFrame()
        return self.modelo.activaciones_por_cuenca()

    # ----------------------------------------------------------------
    # Validación contra SIMMA (opcional, para leyenda en UI)
    # ----------------------------------------------------------------
    def validar_contra_simma(self) -> dict | None:
        """Si el escenario es histórico, valida contra SIMMA y devuelve métricas."""
        if self.modelo is None or self.params.escenario.lower() != "historico":
            return None
        try:
            return validacion.validar_modelo_vs_simma(self.modelo)
        except Exception:
            return None
