"""CuencaAgent: el agente hidrológico del Modelo 1.

Cada cuenca hidrográfica colombiana es un agente autónomo con parámetros
heterogéneos según su área hidrográfica (Caribe, Magdalena-Cauca, Pacífico,
Orinoco, Amazonas).

Las tres reglas de decisión son las del Protocolo ODD:

    1. Precipitación:  P_i(t) = P_{0,i}(mes) + β_{1,i} · ONI(t-1) + ε
    2. Balance:        H_i(t+1) = (1 - κ_i) · H_i(t) + P_i(t+1)
    3. Evento:         E_i(t) = 1  si  H_i(t) > θ_i · C_i

El `ModeloCuencas` orquesta la activación simultánea (todos evalúan antes
de aplicar), lo que requiere una pasada en dos fases:

    - `compute_next_state()`: calcula el próximo H sin aplicar
    - `apply_next_state()`: aplica H y emite evento si corresponde
"""

from __future__ import annotations

from typing import Literal

import mesa
import numpy as np


class CuencaAgent(mesa.Agent):
    """Agente hidrológico con dinámica de balance de humedad.

    Attributes:
        unique_id: identificador heredado de mesa.Agent
        id_cuenca: ID oficial de la zonificación IDEAM/HydroBASINS
        nombre: nombre legible (ej. "Río Magdalena Alto")
        area_hidrografica: 'Caribe', 'Magdalena-Cauca', 'Pacifico', 'Orinoco', 'Amazonas'
        beta_1: sensibilidad ONI → precipitación (mm/mes por °C)
        theta: umbral de activación (fracción de capacidad)
        kappa: tasa de drenaje mensual
        capacidad_hidrica: capacidad máxima de retención (mm)
        precip_climatologia: array [12] de climatología mensual
        humedad: estado actual H(t)
        evento_activo: True si E(t-1) = 1
        historial_humedad: lista de H en cada tick
        historial_eventos: lista de ticks donde E=1
    """

    def __init__(
        self,
        model: "ModeloCuencas",
        id_cuenca: str,
        nombre: str,
        area_hidrografica: str,
        beta_1: float,
        theta: float,
        kappa: float,
        capacidad_hidrica: float = 1000.0,
        precip_climatologia: np.ndarray | None = None,
        humedad_inicial: float = 0.0,
    ) -> None:
        super().__init__(model)
        self.id_cuenca = id_cuenca
        self.nombre = nombre
        self.area_hidrografica = area_hidrografica
        self.beta_1 = beta_1
        self.theta = theta
        self.kappa = kappa
        self.capacidad_hidrica = capacidad_hidrica

        if precip_climatologia is None:
            # Climatología bimodal genérica colombiana (mm/mes)
            precip_climatologia = np.array([
                120, 140, 180, 220, 200, 160,
                140, 140, 170, 220, 200, 150,
            ], dtype=float)
        self.precip_climatologia = precip_climatologia

        self.humedad = humedad_inicial
        self.evento_activo = False
        self._next_humedad: float | None = None
        self._next_evento: bool = False

        self.historial_humedad: list[float] = []
        self.historial_eventos: list[int] = []
        self.historial_precip: list[float] = []

    # ----------------------------------------------------------------
    # Scheduler simultáneo: compute → apply
    # ----------------------------------------------------------------
    def compute_next_state(self) -> None:
        """Fase 1: calcula el siguiente estado sin aplicar.

        Lee ``self.model.oni_actual`` y ``self.model.tick``,
        calcula P(t), H(t+1), E(t). Guarda en atributos privados.
        """
        mes = (self.model.tick % 12) + 1   # 1..12
        p0 = self.precip_climatologia[mes - 1]

        # Ruido estocástico (opcional)
        if self.model.ruido_precip > 0:
            eps = self.model.rng.normal(0, self.model.ruido_precip * p0)
        else:
            eps = 0.0

        # Precipitación = climatología + respuesta ENSO
        oni = self.model.oni_actual if self.model.oni_actual is not None else 0.0
        p_mes = p0 + self.beta_1 * oni + eps
        p_mes = max(p_mes, 0.0)  # no negativa

        # Balance hídrico
        h_next = (1 - self.kappa) * self.humedad + p_mes
        h_next = max(h_next, 0.0)

        # Evento binario
        umbral = self.theta * self.capacidad_hidrica
        evento = h_next > umbral

        self._next_humedad = h_next
        self._next_evento = evento
        self._next_precip = p_mes

    def apply_next_state(self) -> None:
        """Fase 2: aplica el estado calculado en compute_next_state()."""
        if self._next_humedad is None:
            raise RuntimeError(
                f"Cuenca {self.id_cuenca}: apply_next_state() sin compute_next_state() previo"
            )

        self.humedad = self._next_humedad
        self.evento_activo = self._next_evento

        # Registrar en historial
        self.historial_humedad.append(self.humedad)
        self.historial_precip.append(self._next_precip)
        if self.evento_activo:
            self.historial_eventos.append(self.model.tick)

        # Reset para el siguiente tick
        self._next_humedad = None

    # ----------------------------------------------------------------
    # Estado visual (Nivel 3 — NetLogo raster)
    # ----------------------------------------------------------------
    def clasificar_estado(self) -> Literal["estiaje", "normal", "humedo", "saturado"]:
        """Clasifica el estado hídrico en 4 buckets para visualización.

        Thresholds sobre ``humedad / capacidad_hidrica``:
            < 0.25  → estiaje
            < 0.60  → normal
            < theta → humedo
            ≥ theta → saturado
        """
        frac = self.humedad / self.capacidad_hidrica
        if frac < 0.25:
            return "estiaje"
        if frac < 0.60:
            return "normal"
        if frac < self.theta:
            return "humedo"
        return "saturado"

    # ----------------------------------------------------------------
    # Repr
    # ----------------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"<CuencaAgent {self.id_cuenca} ({self.area_hidrografica}) "
            f"β₁={self.beta_1:.1f} θ={self.theta:.2f} κ={self.kappa:.2f} "
            f"H={self.humedad:.0f}/{self.capacidad_hidrica:.0f}>"
        )
