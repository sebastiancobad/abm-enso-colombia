# ABM-ENSO-Colombia

**Modelo Basado en Agentes del sistema climático-hidrológico colombiano bajo forzamiento ENSO**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/sebastiancobad/abm-enso-colombia/releases/tag/v1.0.0)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-70%20passed-brightgreen.svg)](tests/)
[![Mesa 3.x](https://img.shields.io/badge/mesa-3.x-orange.svg)](https://mesa.readthedocs.io/)

Este repositorio implementa el **Modelo 1 (Clima/Cuencas)** del pipeline ABM-UTADEO: un modelo basado en agentes donde cada cuenca hidrográfica es un agente que responde al forzamiento ENSO mediante el Oscilador de Lorenz, calibrado contra datos observados de SIMMA, ERA5 y SIRH.

![Captura de la app](docs/img/app.png)

## Características

- **Pipeline de datos reproducible** — descarga automática de 5 fuentes: ONI/NOAA, ERA5-Land/Copernicus, SIRH/IDEAM, SIMMA/SGC, Cuencas HydroBASINS
- **Calibración estadística completa** — Butterworth banda ENSO (2-7 años), OLS por área hidrográfica, grid search θ/κ con F1 contra SIMMA
- **ABM en Mesa 3.x** — 231 cuencas con scheduler simultáneo y heterogeneidad por región
- **Visualización tipo NetLogo** — app Solara interactiva con mapa de 231 cuencas, series temporales Plotly, heatmap espacio-temporal y periodograma Lomb-Scargle
- **Export GIF/MP4** de simulaciones para reportes y presentaciones
- **Tests exhaustivos** — 70 tests con síntesis en runtime (sin archivos fixture)

## Resultados calibrados (v1.0.0)

| Parámetro | Valor calibrado | Fuente |
|-----------|----------------|--------|
| β₁ (nacional) | **−7.33 mm/mes por °C ONI** | OLS ONI × ERA5 precipitación, lag 1 mes |
| θ* (umbral evento) | **0.700** | Grid search F1 vs SIMMA |
| κ* (drenaje mensual) | **0.275** | Grid search F1 vs SIMMA |
| F1 calibración | **0.629** | 6826 eventos SIMMA 1981-2024 |
| r validación | **0.43** | vs SIMMA 2010-2012 |
| F1 validación | **0.74** | vs SIMMA 2010-2012 |

### Heterogeneidad β₁ por área hidrográfica

| Área | β₁ (mm/mes/°C) | Interpretación |
|------|---------------:|----------------|
| Magdalena-Cauca | −9.5 | Alta sensibilidad ENSO (Andes, vertiente Caribe) |
| Caribe | −8.2 | Respuesta fuerte, estacionalidad marcada |
| Pacífico | −5.8 | Anticorrelación moderada (régimen de vertiente) |
| Orinoco | −4.5 | Respuesta débil, efecto amortiguado |
| Amazonas | −2.0 | Casi neutro (bajo control ENSO) |

> **Nota física:** el signo negativo indica que **El Niño → sequía** y **La Niña → exceso de lluvia** en Colombia (consistente con literatura: Poveda 2004, Hoyos et al. 2013).

## Quickstart

### Instalación (recomendado: Miniforge/conda)

```bash
git clone https://github.com/sebastiancobad/abm-enso-colombia.git
cd abm-enso-colombia
conda env create -f environment.yml
conda activate abm-enso
```

### Pipeline completo en 3 comandos

```bash
# 1. Descargar las 5 fuentes de datos (~30-45 min, cuenta Copernicus requerida)
abm-enso download

# 2. Calibrar β₁, θ, κ contra SIMMA
abm-enso calibrate

# 3. Lanzar la app interactiva en el navegador
abm-enso viz
```

### Correr un escenario en modo script

```bash
# Simulación de La Niña 2010-2011 con 30 réplicas Monte Carlo
abm-enso simulate --scenario nina-2010 --meses 36 --replicas 30 --ruido 15

# Validar modelo contra SIMMA histórico 2010-2012
abm-enso simulate --scenario historico --meses 36 --validar
```

## Estructura del repositorio

```
abm-enso-colombia/
├── src/abm_enso/
│   ├── data/          # 5 clientes de datos (oni, era5, sirh, simma, cuencas)
│   ├── analysis/      # filtros, Lorenz, calibración β/θ/κ, métricas
│   ├── model/         # CuencaAgent, ModeloCuencas, escenarios, validación
│   ├── viz/           # App Solara tipo NetLogo (mapa + series + exports)
│   ├── utils/         # paths, constantes
│   ├── cli.py         # entry point `abm-enso`
│   └── pipeline.py    # orquestador end-to-end
├── notebooks/         # 01 exploración, 02 calibración, 03 simulación
├── tests/             # 70 tests (smoke + data + analysis + model + viz)
├── docs/              # mkdocs (deploy en GitHub Pages)
├── data/raw/          # datos descargados (gitignored)
├── outputs/           # GIFs/MP4/figuras generadas
├── environment.yml    # entorno conda-forge
└── pyproject.toml     # setuptools + dependencias + ruff/mypy/pytest
```

## Comandos principales

| Comando | Qué hace |
|---------|----------|
| `abm-enso download` | Descarga ONI, ERA5, SIRH, SIMMA, Cuencas |
| `abm-enso download --solo era5 --era5-chunk-years 2` | Sólo ERA5 en chunks pequeños (evita cost limit) |
| `abm-enso calibrate` | Recalcula β₁, θ, κ y guarda `data/processed/cuencas_parametros.parquet` |
| `abm-enso simulate --scenario <nina-2010\|nino-2015\|neutro\|historico\|lorenz>` | Corre el ABM con el escenario indicado |
| `abm-enso viz` | Lanza la app Solara en `http://127.0.0.1:8765` |

## Documentación completa

- **Docs navegables:** [sebastiancobad.github.io/abm-enso-colombia](https://sebastiancobad.github.io/abm-enso-colombia/)
- **Quickstart extendido:** [`docs/quickstart.md`](docs/quickstart.md)
- **Descripción ODD del modelo:** [`docs/teoria/odd.md`](docs/teoria/odd.md)
- **Fundamentos ENSO-Lorenz:** [`docs/teoria/enso-lorenz.md`](docs/teoria/enso-lorenz.md)
- **Referencia por módulo:** [`docs/modulos/`](docs/modulos/)

## Testing

```bash
pytest tests/ -v
```

**70/70 tests pasando** (4 smoke + 11 data + 21 analysis + 19 model + 15 viz).

## Cita académica

Si usas este software en tu investigación, cítalo así:

```bibtex
@software{coba_abm_enso_colombia_2026,
  author  = {Coba Daza, Sebastián},
  title   = {ABM-ENSO-Colombia: Agent-Based Model of Colombian Hydrology Under ENSO Forcing},
  year    = {2026},
  version = {1.0.0},
  url     = {https://github.com/sebastiancobad/abm-enso-colombia},
  license = {MIT},
}
```

También existe [`CITATION.cff`](CITATION.cff) para GitHub.

## Licencia

MIT — ver [`LICENSE`](LICENSE).

## Contexto académico

Este repositorio corresponde al Modelo 1 del trabajo de grado *Modelado del impacto de ENSO sobre la red vial colombiana mediante agentes simultáneos* (UTADEO, 2026). Los otros 3 modelos (opinión pública, red vial, INVIAS) están fuera del alcance de este repo.

## Créditos de datos

- **ONI:** NOAA Climate Prediction Center, *Oceanic Niño Index*, mensual, 1950-presente.
- **ERA5-Land:** Copernicus Climate Change Service (C3S), Muñoz Sabater (2019). Contains modified Copernicus Climate Change Service information 2026.
- **SIMMA:** Servicio Geológico Colombiano, Sistema de Información de Movimientos en Masa.
- **SIRH:** IDEAM, Sistema de Información del Recurso Hídrico (datos.gov.co vía Socrata).
- **Cuencas:** HydroBASINS nivel 6 (Lehner & Grill, 2013), recortado a territorio colombiano. *Fallback de IDEAM ArcGIS Hub.*

## Contribuir

Pull requests bienvenidas. Por favor asegúrate de que los tests pasen (`pytest tests/`) antes de enviar.

---

_Desarrollado con ayuda de Claude y mucho café ☕_
