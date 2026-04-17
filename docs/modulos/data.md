# Módulo `data`

> **Estado:** pendiente de implementación en [Fase 2](../roadmap.md#fase-2--pipeline-de-datos).

Este subpaquete refactoriza los cuatro scripts originales (`Fuente_1.py` a `Fuente_4.py`) en módulos Python parametrizados, con tests y caché local.

## Estructura prevista

```
src/abm_enso/data/
├── __init__.py
├── oni.py           # NOAA/CPC — descarga y parsing del ONI
├── era5.py          # Copernicus CDS — precip, humedad, runoff
├── sirh.py          # IDEAM/Socrata — nivel hidrométrico
├── simma.py         # SGC — inventario de movimientos en masa
└── cuencas.py       # IDEAM/ArcGIS Hub — shapefile de cuencas
```

## API esperada

Cada módulo expone una función `load_*()` que devuelve un DataFrame o GeoDataFrame limpio:

```python
from abm_enso.data import oni, era5, sirh, simma, cuencas

df_oni      = oni.load(start=1981, end=2024)
df_era5     = era5.load(variable="tp")
df_sirh     = sirh.load(estaciones=["0035077180"])
df_simma    = simma.load(tipo="Deslizamiento", filtrar_pdf=True)
gdf_cuencas = cuencas.load()
```

Todas las funciones aceptan `use_cache=True` por defecto.

## Detalles de implementación

- **`oni.py`** — reusa la lógica del `Fuente_1.py` original (parsing del archivo plano NOAA) con mejor manejo de errores
- **`era5.py`** — cliente Copernicus CDS con reintentos y resume downloads; cache en `data/raw/era5_*.nc`
- **`sirh.py`** — cliente Socrata con bloques anuales (evita timeouts), reusa el patrón del `Fuente_3.py`
- **`simma.py`** — carga del CSV incluido en el repo + limpieza de nombres partidos (`CUNDINAMA RCA` → `CUNDINAMARCA`)
- **`cuencas.py`** — estrategia 3-tier: ArcGIS Hub → SIAC → HydroBASINS, con verificación de integridad
