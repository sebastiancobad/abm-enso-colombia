# ABM-ENSO-Colombia

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Mesa](https://img.shields.io/badge/mesa-2.3+-green.svg)](https://mesa.readthedocs.io/)
[![Status](https://img.shields.io/badge/status-work%20in%20progress-orange.svg)]()

> **Modelado Basado en Agentes (ABM) del sistema climático-hidrológico colombiano bajo forzamiento ENSO.**
> Modelo 1 del pipeline ABM-UTADEO: cuencas hidrográficas como agentes heterogéneos acoplados al ciclo El Niño/La Niña via oscilador de Lorenz.

---

## ¿Qué hace este proyecto?

Responde a una pregunta concreta:

> **¿Puede un ABM calibrado con datos públicos reproducir el patrón espacio-temporal de activaciones hídricas en Colombia durante La Niña 2010-11?**

El modelo encadena cuatro componentes:

1. **Forzamiento externo (ENSO)** — Oscilador de Lorenz calibrado contra el índice ONI de NOAA/CPC para generar trayectorias pseudo-periódicas sintéticas del ciclo El Niño/La Niña.
2. **Precipitación local por cuenca** — Regresión OLS ONI × ERA5-Land calibrada por tipo de suelo, $P(t) = P_0 + \beta_1 \cdot \text{ONI}(t)$.
3. **Balance hídrico del suelo** — Acumulación con drenaje exponencial, $H(t+1) = (1-\kappa) \cdot H(t) + P(t+1)$.
4. **Disparo de evento** — Activación binaria al cruzar un umbral, $E(t) = \mathbb{1}\{H(t) > \theta\}$.

Cada cuenca es un agente Mesa con parámetros heterogéneos ($\beta_1$, $\theta$, $\kappa$, capacidad) y los eventos simulados se validan contra el inventario SIMMA del Servicio Geológico Colombiano.

---

## Arquitectura

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Fuentes de dato │ ───▶ │  Análisis +      │ ───▶ │  ABM en Mesa     │
│  ONI · ERA5 ·    │      │  Calibración     │      │  N cuencas ×     │
│  SIRH · SIMMA    │      │  OLS · Grid + F1 │      │  T meses         │
└──────────────────┘      └──────────────────┘      └──────────────────┘
                                                             │
                                                             ▼
                                                  ┌──────────────────┐
                                                  │ Visualización    │
                                                  │ Solara tipo      │
                                                  │ NetLogo          │
                                                  └──────────────────┘
```

---

## Inicio rápido

### 1. Instalación

```bash
git clone https://github.com/sebastiancobad/abm-enso-colombia.git
cd abm-enso-colombia
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Descarga de datos (una sola vez)

```bash
python scripts/download_all.py
```

Este comando obtiene:

| Fuente | Origen | Tamaño aprox. |
|--------|--------|---------------|
| ONI mensual | NOAA/CPC (HTTPS) | ~20 KB |
| ERA5-Land (precip, humedad, runoff) | Copernicus CDS (API) | ~15 MB |
| Nivel hidrométrico SIRH | datos.gov.co (Socrata API) | ~50 MB |
| Inventario SIMMA | CSV incluido en `data/raw/` | 700 KB |
| Cuencas IDEAM (shapefile) | ArcGIS Hub / HydroBASINS (fallback) | ~30 MB |

> **Nota Copernicus:** ERA5 requiere cuenta gratuita y archivo `~/.cdsapirc`. Ver [docs/instalacion.md](docs/instalacion.md).

### 3. Correr el pipeline completo

```bash
python -m abm_enso.pipeline --escenario nina-2010
```

### 4. Abrir la simulación interactiva

```bash
solara run src/abm_enso/viz/app.py
```

Se abre un navegador con la grilla de cuencas coloreadas por estado hídrico, controles play/pause/step, sliders para $\theta$, $\kappa$, $\beta_1$, y series temporales sincronizadas.

---

## Estructura del repositorio

```
abm-enso-colombia/
├── data/
│   ├── raw/              # datos originales sin procesar
│   ├── processed/        # datos limpios listos para análisis
│   └── external/         # shapefiles, climatologías
├── docs/                 # mkdocs (teoría, ODD, tutoriales)
├── notebooks/            # Jupyter (exploración, calibración, validación)
├── src/abm_enso/
│   ├── data/             # módulos de carga y preparación
│   ├── analysis/         # filtro Butterworth, Lorenz, calibración
│   ├── model/            # CuencaAgent, ModeloCuencas
│   ├── viz/              # Solara app + helpers matplotlib
│   └── utils/            # constantes, tipos, paths
├── scripts/              # entry points CLI
├── tests/                # pytest
└── outputs/              # figuras y resultados de simulación
```

---

## Documentación

La documentación completa (mkdocs) cubre:

- **Teoría**: propiedades de los agentes, ENSO como sistema caótico, protocolo ODD
- **Módulos**: guía detallada de cada subpaquete
- **Tutoriales**: desde cero hasta escenarios climáticos 2025-2030
- **API Reference**: docstrings autogenerados

Para generarla localmente:

```bash
mkdocs serve
```

---

## Fuentes de datos y atribución

| Fuente | Proveedor | Licencia |
|--------|-----------|----------|
| ONI (Oceanic Niño Index) | NOAA Climate Prediction Center | Public domain |
| ERA5-Land | Copernicus Climate Data Store / ECMWF | Copernicus License |
| SIRH (nivel hidrométrico) | IDEAM vía datos.gov.co | Datos abiertos Colombia |
| SIMMA (movimientos en masa) | Servicio Geológico Colombiano | Datos abiertos Colombia |
| Zonificación hidrográfica | IDEAM / HydroSHEDS | CC-BY-4.0 |

---

## Citación

Si usas este código en publicaciones académicas:

```bibtex
@software{coba2026abmenso,
  author  = {Coba Daza, Sebastián},
  title   = {ABM-ENSO-Colombia: Modelo Basado en Agentes del Sistema Climático-Hidrológico Colombiano},
  year    = {2026},
  url     = {https://github.com/sebastiancobad/abm-enso-colombia}
}
```

---

## Licencia

MIT — ver [LICENSE](LICENSE).

## Reconocimientos

Desarrollado en el marco del curso **Modelado Basado en Agentes** — UTADEO. Basado en la arquitectura de pipeline ABM diseñada para integrar los cuatro modelos: Clima, Red Vial, Dinámica de Opinión, y Decisión INVIAS.
