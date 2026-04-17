"""Subpaquete `data`: carga y descarga de las 5 fuentes del Modelo 1.

Módulos:
    oni       — NOAA/CPC, índice ONI mensual
    era5      — Copernicus CDS, ERA5-Land precip/humedad/runoff
    sirh      — IDEAM vía Socrata, nivel hidrométrico
    simma     — SGC, inventario de movimientos en masa
    cuencas   — IDEAM, zonificación hidrográfica

Cada módulo expone `load(...)` (DataFrame listo para usar) y un
`download(...)` que baja los datos crudos a `data/raw/` con cache.
"""

from abm_enso.data import cuencas, era5, oni, simma, sirh

__all__ = ["oni", "era5", "sirh", "simma", "cuencas"]
