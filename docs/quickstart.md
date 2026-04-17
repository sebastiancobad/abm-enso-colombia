# Quickstart

Pipeline completo end-to-end en ~1 hora (mayor parte esperando descargas).

## Prerrequisitos

- Miniforge / Anaconda instalado ([descarga](https://github.com/conda-forge/miniforge/releases/latest))
- Cuenta gratuita en [Copernicus CDS](https://cds.climate.copernicus.eu/user/register) para ERA5

## 1. Clonar y crear entorno

```bash
git clone https://github.com/sebastiancobad/abm-enso-colombia.git
cd abm-enso-colombia
conda env create -f environment.yml
conda activate abm-enso
```

## 2. Configurar Copernicus (solo la primera vez)

Copia tu API key desde https://cds.climate.copernicus.eu/user hacia `~/.cdsapirc`:

```
url: https://cds.climate.copernicus.eu/api
key: tu-key-aqui
```

Acepta términos del dataset ERA5-Land en [esta página](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=download).

## 3. Descargar datos (~30–45 min)

```bash
abm-enso download --skip-on-error
```

Si Copernicus rechaza ERA5 por cost limit, baja el tamaño del chunk:

```bash
abm-enso download --solo era5 --era5-chunk-years 2 --force
```

Al terminar, `data/raw/` contendrá:

| Archivo | Contenido |
|---------|-----------|
| `oni_mensual.csv` | ONI NOAA 1950–presente |
| `era5_stepType-avgad.nc` | Flujos ERA5 (tp, ro) |
| `era5_stepType-avgua.nc` | Estado ERA5 (swvl1) |
| `nivel_sirh_diario.csv` | Nivel hidrométrico SIRH |
| `Resultados_SIMMA.csv` | 6826 eventos de movimientos en masa |
| `cuencas_colombia.gpkg` | 231 polígonos HydroBASINS |

## 4. Calibrar el modelo

```bash
abm-enso calibrate
```

Output esperado (valores reales calibrados):

```
[1/5] Cargando datos...
[2/5] Filtrando señal ENSO (Butterworth 2-7 años)...
[3/5] Calibrando Lorenz al ONI filtrado...
       r(Lorenz, ONI_filtrado) = 0.042
[4/5] Calibrando β₁ con OLS...
       β₁ = -7.33 mm/mes por °C ONI
       r² = 0.176
[5/5] Grid search θ, κ contra eventos SIMMA...
       θ* = 0.700
       κ* = 0.275
       F1 = 0.629
✓ Parámetros guardados en data/processed/cuencas_parametros.parquet
```

## 5. Lanzar la app interactiva

```bash
abm-enso viz
```

El navegador se abre en `http://127.0.0.1:8765` con el dashboard completo:

- Dashboard superior con tick · fecha · ONI · % activadas
- Mapa choropleth de 231 cuencas (matplotlib)
- Series temporales sincronizadas (ONI, activadas, humedad, SIMMA)
- Heatmap cuencas × tiempo
- Periodograma Lomb-Scargle con banda ENSO

## 6. Correr escenarios en batch

```bash
# La Niña 2010-2011 con 30 réplicas Monte Carlo
abm-enso simulate --scenario nina-2010 --replicas 30 --ruido 15

# El Niño 2015-2016
abm-enso simulate --scenario nino-2015 --replicas 30 --ruido 15

# Validación contra SIMMA histórico
abm-enso simulate --scenario historico --meses 36 --validar
```

## 7. Notebooks Jupyter

Para explorar de forma interactiva:

```bash
jupyter lab notebooks/02_calibracion.ipynb
```

Los 3 notebooks cubren:

- `01_exploracion_datos.ipynb` — visualización de las 5 fuentes
- `02_calibracion.ipynb` — pipeline completo + panel interactivo Plotly
- `03_simulacion.ipynb` — comparación Niña vs Niño vs neutro + Monte Carlo

## Troubleshooting

### `conda env create` falla con SSL o paquete no encontrado

Algunas redes corporativas bloquean conda-forge. Usa `pip install -e .` como alternativa (requiere GDAL/GEOS preinstalados en el sistema).

### Copernicus: `403 Forbidden` o `cost limits exceeded`

Acepta los términos del dataset ERA5-Land (ver paso 2) y baja el chunk:

```bash
abm-enso download --solo era5 --era5-chunk-years 2
```

### Solara: `ModuleNotFoundError: No module named 'anywidget'`

Dependencia perdida. Instalar:

```bash
pip install anywidget ipywidgets
```

### La app es lenta con 231 cuencas

Es esperado. Cada tick redibuja 231 polígonos matplotlib. Opciones:

- Bajar velocidad a 1 tick/seg
- Usar `--scenario neutro` (series más cortas)
- Para exports fluidos, considera generar GIF en vez de ver en vivo
