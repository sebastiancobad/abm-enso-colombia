# Módulo `data`

Clientes para las 5 fuentes de datos del pipeline.

## Arquitectura

Cada submódulo sigue el mismo patrón:

```python
from abm_enso.data import oni

oni.download(force=False)   # Descarga a data/raw/ si no existe
df = oni.load()             # Carga el archivo a DataFrame
```

## `oni` — Oceanic Niño Index

**Fuente:** NOAA Climate Prediction Center ([enlace](https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php))

- Resolución: mensual, 1950–presente
- Formato: ASCII de ancho fijo parseado a `pd.DataFrame`
- Caché: `data/raw/oni_mensual.csv`

```python
from abm_enso.data import oni
df = oni.load()
df.head()
#         oni  season
# 1950-01  -1.53  DJF
# 1950-02  -1.34  JFM
# ...
```

## `era5` — ERA5-Land (Copernicus)

**Fuente:** ECMWF vía CDS API ([enlace](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land))

- Variables: `total_precipitation` (tp), `runoff` (ro), `volumetric_soil_water_layer_1` (swvl1)
- Resolución espacial: 0.1° nativa, agregada a nacional
- Resolución temporal: mensual (reagrega daily)
- Tamaño: ~150 MB para 1981–2024
- Caché: `data/raw/era5_stepType-avgad.nc` (flujos) + `era5_stepType-avgua.nc` (estado)

### Chunking por bloques

Para evitar el cost limit de Copernicus (~50k elementos/request), la descarga se divide en bloques de `chunk_years` años y se concatena al final con `xarray`:

```bash
abm-enso download --solo era5 --era5-chunk-years 5
```

Si aún falla, bajar a 2–3.

## `sirh` — Sistema de Información del Recurso Hídrico (IDEAM)

**Fuente:** datos.gov.co vía Socrata Open Data API

- 3 estaciones piloto: Culima (0035077180), Río Claro (0026157190), La Mora (0021167080)
- Variable: nivel hidrométrico diario
- Caché: `data/raw/nivel_sirh_diario.csv`

## `simma` — Sistema de Información de Movimientos en Masa (SGC)

**Fuente:** Servicio Geológico Colombiano

Estrategia híbrida:

1. **Primera opción:** descarga del CSV oficial SGC (13 columnas, sin fecha)
2. **Fallback:** CSV local versionado extraído de PDFs (6826 eventos con fecha y tipo)

El fallback es siempre necesario porque el CSV oficial no tiene columna de fecha.

```python
from abm_enso.data import simma
df = simma.load(tipo=['Deslizamiento', 'Flujo'])
# → 6826 filas con columnas: fecha_evento, tipo, departamento, municipio, ...
```

## `cuencas` — Cuencas hidrográficas IDEAM

**Fuente:** estrategia 3-tier con fallback garantizado

1. ArcGIS Hub IDEAM (cuencas oficiales)
2. **HydroBASINS** nivel 6 global (Lehner & Grill 2013) → recortado a Colombia (default)
3. Sintético de emergencia (solo para testing)

- 231 polígonos con columnas: `id_cuenca`, `nombre`, `area_hidrografica`, `area_km2`, `geometry`
- CRS: EPSG:4326
- Caché: `data/raw/cuencas_colombia.gpkg` (GeoPackage)

## API pública

::: abm_enso.data
    options:
      show_root_heading: false
      show_source: false
      members:
        - oni
        - era5
        - sirh
        - simma
        - cuencas
