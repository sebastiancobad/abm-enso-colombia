# Quickstart

Pipeline completo end-to-end en cinco comandos, asumiendo que la [instalación](instalacion.md) ya está hecha.

## 1. Descargar todas las fuentes

```bash
abm-enso download
```

Esto descarga (una sola vez):

- ONI mensual de NOAA/CPC → `data/raw/oni_mensual.csv`
- ERA5-Land vía Copernicus CDS → `data/raw/era5_*.nc`
- SIRH (3 estaciones piloto) vía Socrata API → `data/raw/nivel_sirh_diario.csv`
- Inventario SIMMA (ya incluido en el repo) → `data/raw/Resultados_SIMMA.csv`
- Cuencas IDEAM vía ArcGIS Hub → `data/raw/cuencas_colombia.gpkg`

Duración aproximada: **25–40 min** (depende principalmente de los tiempos de respuesta del Copernicus CDS y de la API Socrata).

## 2. Calibrar los parámetros

```bash
abm-enso calibrate
```

Este comando:

- Filtra la señal ENSO de las 4 fuentes con Butterworth banda 2–7 años
- Ajusta el oscilador de Lorenz al ONI observado
- Estima $\beta_1$ por tipo de suelo vía OLS (ONI × ERA5 precipitación)
- Busca en grilla $\theta$ y $\kappa$ maximizando el F1-score contra el catálogo SIMMA
- Guarda los parámetros calibrados en `data/processed/cuencas_parametros.parquet`
- Genera figuras de diagnóstico en `outputs/figures/`

Duración aproximada: **3–5 min**.

## 3. Simular el ABM

```bash
abm-enso simulate --scenario nina-2010 --meses 60 --replicas 30
```

Escenarios disponibles:

- `nina-2010` — reproduce La Niña 2010-11 (validación)
- `nino-2015` — El Niño 2015-16
- `neutro` — condiciones ENSO-neutrales (baseline)
- `custom` — lee `config/custom_scenario.yaml`

Output: serie temporal de activaciones por cuenca + métricas agregadas en `outputs/simulations/`.

## 4. Abrir la visualización interactiva

```bash
abm-enso viz
```

Abre un navegador con:

- Mapa de cuencas coloreadas por estado hídrico (estiaje / normal / húmedo / saturado)
- Controles play / pause / step / reset
- Sliders interactivos para $\theta$, $\kappa$, $\beta_1$
- Serie temporal del ONI y estado agregado
- Botón de export a GIF

## 5. Ver la documentación offline

```bash
mkdocs serve
```

Luego abre `http://127.0.0.1:8000` en tu navegador.
