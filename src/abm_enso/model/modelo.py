"""ModeloCuencas: el contenedor del ABM hidrológico.

Orquesta la simulación de N cuencas bajo forzamiento ENSO durante T meses.

Por cada tick:
    1. Actualiza ``oni_actual`` desde la serie de forzamiento
    2. Scheduler simultáneo (dos fases):
       - Fase A: todas las cuencas calculan su próximo estado
       - Fase B: todas aplican el nuevo estado
    3. DataCollector registra métricas agregadas y por agente

Heterogeneidad de β₁ por área hidrográfica IDEAM:
    Caribe, Magdalena-Cauca, Pacifico, Orinoco, Amazonas.

Los parámetros (β₁_por_area, θ, κ) se leen de
``data/processed/cuencas_parametros.parquet`` si existe, sino usa defaults.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import mesa
import numpy as np
import pandas as pd

from abm_enso.model.agente import CuencaAgent


# ==========================================================
# β₁ por área hidrográfica (negativo: La Niña → +lluvia)
# ==========================================================
# Calibración Fase 3 nacional: -7.33 mm/mes por °C ONI
# Heterogeneizamos por área según literatura (Poveda 2004):
#   Caribe, Andes (Magdalena-Cauca) → respuesta fuerte
#   Pacífico → respuesta moderada (anticorrelación a veces)
#   Orinoco → respuesta débil
#   Amazonas → casi neutro
BETA1_POR_AREA_DEFAULT: dict[str, float] = {
    "Magdalena-Cauca": -9.5,
    "Caribe":          -8.2,
    "Pacifico":        -5.8,
    "Orinoco":         -4.5,
    "Amazonas":        -2.0,
    "default":         -7.3,   # fallback
}


class ModeloCuencas(mesa.Model):
    """ABM de N cuencas bajo forzamiento ONI mensual.

    Args:
        gdf_cuencas: GeoDataFrame con columnas ``id_cuenca``, ``nombre``,
                     ``area_hidrografica`` (+ geometry opcional)
        oni_serie: pd.Series mensual del ONI (real o sintético de Lorenz)
        beta1_por_area: dict {area: β₁}. Si None, usa defaults
        theta: umbral de activación (fracción de capacidad)
        kappa: tasa de drenaje mensual
        ruido_precip: desviación estándar del ruido ε en P(t)
                      como fracción de la climatología (default 0 = determinista)
        seed: semilla para reproducibilidad
    """

    def __init__(
        self,
        gdf_cuencas,
        oni_serie: pd.Series,
        beta1_por_area: dict[str, float] | None = None,
        theta: float = 0.78,
        kappa: float = 0.22,
        ruido_precip: float = 0.0,
        seed: int = 42,
    ) -> None:
        super().__init__(seed=seed)

        self.oni_serie = oni_serie
        self.theta = theta
        self.kappa = kappa
        self.ruido_precip = ruido_precip
        self.beta1_por_area = beta1_por_area or BETA1_POR_AREA_DEFAULT

        # Alias de conveniencia (Mesa ya trae self.random y self._seed)
        self.rng = np.random.default_rng(seed)
        self.tick = 0
        self.oni_actual: float | None = None

        # Crear agentes a partir del GeoDataFrame
        self._crear_agentes(gdf_cuencas)

        # Métricas agregadas en historial
        self.historial_activaciones: list[int] = []
        self.historial_humedad_media: list[float] = []
        self.historial_oni: list[float] = []

    # ----------------------------------------------------------------
    # Inicialización
    # ----------------------------------------------------------------
    def _crear_agentes(self, gdf) -> None:
        """Instancia un CuencaAgent por cada fila del GeoDataFrame."""
        for _, row in gdf.iterrows():
            area = row.get("area_hidrografica", "default")
            beta_1 = self.beta1_por_area.get(area, self.beta1_por_area["default"])

            # Capacidad hídrica varía levemente por área (proxy de tipo de suelo)
            capacidad = {
                "Magdalena-Cauca": 900.0,
                "Caribe":          750.0,
                "Pacifico":        1100.0,
                "Orinoco":         850.0,
                "Amazonas":        1200.0,
            }.get(area, 1000.0)

            CuencaAgent(
                model=self,
                id_cuenca=str(row["id_cuenca"]),
                nombre=row.get("nombre", f"Cuenca_{row['id_cuenca']}"),
                area_hidrografica=area,
                beta_1=beta_1,
                theta=self.theta,
                kappa=self.kappa,
                capacidad_hidrica=capacidad,
                # Humedad inicial: 30% de capacidad (estado neutro)
                humedad_inicial=0.3 * capacidad,
            )

    # ----------------------------------------------------------------
    # Step — activación simultánea (dos fases)
    # ----------------------------------------------------------------
    def step(self) -> None:
        """Avanza un tick (un mes) en el modelo completo."""
        # Actualizar forzamiento ONI desde la serie
        if self.tick < len(self.oni_serie):
            self.oni_actual = float(self.oni_serie.iloc[self.tick])
        else:
            self.oni_actual = 0.0  # más allá de la serie, ENSO-neutral

        # Fase A: todas las cuencas calculan su nuevo estado
        self.agents.do("compute_next_state")

        # Fase B: todas aplican (sincrónico)
        self.agents.do("apply_next_state")

        # Registrar métricas agregadas
        n_activas = sum(1 for a in self.agents if a.evento_activo)
        h_media = float(np.mean([a.humedad for a in self.agents]))
        self.historial_activaciones.append(n_activas)
        self.historial_humedad_media.append(h_media)
        self.historial_oni.append(self.oni_actual)

        self.tick += 1

    def run(self, n_steps: int | None = None) -> None:
        """Corre la simulación completa hasta agotar la serie ONI o n_steps."""
        if n_steps is None:
            n_steps = len(self.oni_serie)
        for _ in range(n_steps):
            self.step()

    # ----------------------------------------------------------------
    # Output — series de tiempo listas para plotear
    # ----------------------------------------------------------------
    def resumen_temporal(self) -> pd.DataFrame:
        """Serie temporal agregada: un renglón por tick.

        Returns:
            DataFrame con columnas: ``tick``, ``fecha``, ``oni``,
            ``n_activaciones``, ``humedad_media``.
        """
        n_registros = len(self.historial_activaciones)
        if n_registros == 0:
            return pd.DataFrame()

        fechas = self.oni_serie.index[:n_registros]
        return pd.DataFrame({
            "tick":           range(n_registros),
            "fecha":          fechas,
            "oni":            self.historial_oni,
            "n_activaciones": self.historial_activaciones,
            "humedad_media":  self.historial_humedad_media,
        })

    def estado_actual_por_cuenca(self) -> pd.DataFrame:
        """Estado presente de cada cuenca (para visualización)."""
        return pd.DataFrame([
            {
                "id_cuenca":         a.id_cuenca,
                "nombre":            a.nombre,
                "area_hidrografica": a.area_hidrografica,
                "humedad":           a.humedad,
                "capacidad":         a.capacidad_hidrica,
                "frac":              a.humedad / a.capacidad_hidrica,
                "evento":            a.evento_activo,
                "estado":            a.clasificar_estado(),
                "beta_1":            a.beta_1,
            }
            for a in self.agents
        ])

    def activaciones_por_cuenca(self) -> pd.DataFrame:
        """Total de activaciones acumuladas por cuenca durante toda la corrida."""
        return pd.DataFrame([
            {
                "id_cuenca":         a.id_cuenca,
                "nombre":            a.nombre,
                "area_hidrografica": a.area_hidrografica,
                "n_eventos":         len(a.historial_eventos),
                "fechas_eventos":    a.historial_eventos.copy(),
            }
            for a in self.agents
        ])


# ==========================================================
# Factory helper: construir modelo desde disco
# ==========================================================
def construir_desde_disco(
    oni_serie: pd.Series | None = None,
    usar_lorenz: bool = False,
    seed: int = 42,
    ruido_precip: float = 0.0,
) -> ModeloCuencas:
    """Factory: carga cuencas de disco + usa parámetros calibrados si existen.

    Args:
        oni_serie: serie ONI a usar. Si ``None``, carga la del disco.
        usar_lorenz: si True, genera ONI sintético con Lorenz en vez de usar
                     el observado
        seed, ruido_precip: parámetros del modelo

    Returns:
        ``ModeloCuencas`` listo para correr con ``.run()``
    """
    from abm_enso.data import cuencas as cuencas_mod, oni as oni_mod
    from abm_enso.utils import paths as _paths

    gdf = cuencas_mod.load()

    if oni_serie is None:
        df_oni = oni_mod.load()
        oni_serie = df_oni["oni"].dropna()

    if usar_lorenz:
        from abm_enso.analysis import filtros, lorenz
        oni_filt = filtros.butterworth_enso(oni_serie)
        oni_serie = lorenz.generar_oni_sintetico(oni_filt, T=2000.0, seed=seed)

    # Cargar parámetros calibrados si existen
    theta = 0.78
    kappa = 0.22
    params_path = _paths.DATA_PROCESSED / "cuencas_parametros.parquet"
    if params_path.exists():
        df_params = pd.read_parquet(params_path)
        if len(df_params) > 0:
            theta = float(df_params.iloc[0]["theta"])
            kappa = float(df_params.iloc[0]["kappa"])

    return ModeloCuencas(
        gdf_cuencas=gdf,
        oni_serie=oni_serie,
        theta=theta,
        kappa=kappa,
        seed=seed,
        ruido_precip=ruido_precip,
    )
