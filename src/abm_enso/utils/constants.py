"""Constantes del modelo: dominio espacial, tipos de suelo, parámetros Lorenz.

Cualquier valor numérico que aparezca en más de un módulo debe vivir aquí
para mantener una sola fuente de verdad.
"""

from __future__ import annotations

from typing import Final

# ==========================================================
# Dominio espacial — Colombia continental
# ==========================================================
COLOMBIA_BBOX: Final[tuple[float, float, float, float]] = (-80.0, -5.0, -66.0, 13.0)
"""Bounding box (lon_min, lat_min, lon_max, lat_max) para Colombia continental."""

COLOMBIA_AREA_ERA5: Final[list[float]] = [13, -80, -5, -66]
"""Orden [N, W, S, E] requerido por el API de Copernicus CDS."""


# ==========================================================
# Rango temporal
# ==========================================================
YEAR_START: Final[int] = 1981
"""Primer año del período de análisis (ERA5 empieza en 1940 pero calibramos desde 1981)."""

YEAR_END: Final[int] = 2024

YEAR_CALIBRATION_END: Final[int] = 2009
"""Último año del período de calibración. 2010-2024 queda para validación."""


# ==========================================================
# ENSO — umbrales oficiales NOAA/CPC
# ==========================================================
UMBRAL_NINA: Final[float] = -0.5
"""ONI ≤ -0.5 °C clasifica como La Niña (5 meses consecutivos para evento oficial)."""

UMBRAL_NINO: Final[float] = 0.5


# ==========================================================
# Filtro Butterworth — banda ENSO
# ==========================================================
BUTTERWORTH_ORDER: Final[int] = 4
BUTTERWORTH_LOW_CYCLES_PER_YEAR: Final[float] = 1 / 7   # período 7 años
BUTTERWORTH_HIGH_CYCLES_PER_YEAR: Final[float] = 1 / 2  # período 2 años


# ==========================================================
# Oscilador de Lorenz — parámetros canónicos
# ==========================================================
LORENZ_SIGMA: Final[float] = 10.0
"""Número de Prandtl."""

LORENZ_RHO: Final[float] = 28.0
"""Número de Rayleigh."""

LORENZ_BETA: Final[float] = 8.0 / 3.0
"""Relación geométrica."""

LORENZ_INIT: Final[tuple[float, float, float]] = (1.0, 1.0, 1.0)
"""Condiciones iniciales estándar."""


# ==========================================================
# Tipos de suelo — β₁ calibrado (mm/mes por °C ONI, valores iniciales del PPT)
# ==========================================================
TIPOS_SUELO: Final[tuple[str, ...]] = ("arcilloso", "arenoso", "rocoso")

BETA1_DEFAULT: Final[dict[str, float]] = {
    "arcilloso": 1.82,   # alta retención → respuesta fuerte y sostenida
    "arenoso":   1.31,   # drenaje rápido → respuesta moderada
    "rocoso":    0.94,   # escasa infiltración → respuesta baja
}

# ==========================================================
# Umbral y drenaje — valores iniciales del PPT (recalibrados por el pipeline)
# ==========================================================
THETA_DEFAULT: Final[float] = 0.78
"""Fracción de capacidad hídrica que activa riesgo."""

KAPPA_DEFAULT: Final[float] = 0.22
"""Tasa de drenaje mensual — 22% del nivel se drena sin lluvia."""


# ==========================================================
# Estados hídricos de la cuenca (Nivel 3 — visualización NetLogo)
# ==========================================================
ESTADOS_HIDRICOS: Final[tuple[str, ...]] = ("estiaje", "normal", "humedo", "saturado")

ESTADO_COLORES: Final[dict[str, str]] = {
    "estiaje":  "#B45309",   # naranja-marrón
    "normal":   "#D1D5DB",   # gris claro
    "humedo":   "#60A5FA",   # azul medio
    "saturado": "#DC2626",   # rojo
}


# ==========================================================
# Validación — evento de referencia
# ==========================================================
NINA_2010_START: Final[str] = "2010-06-01"
NINA_2010_END: Final[str] = "2011-05-01"
