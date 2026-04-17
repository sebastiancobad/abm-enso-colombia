# Roadmap

El proyecto avanza en **6 fases** secuenciales. Cada fase termina con un punto de revisión y un entregable verificable antes de pasar a la siguiente.

## Estado actual

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Esqueleto del repo + docs base | 🟢 En curso |
| 2 | Pipeline de datos (4 fuentes + cuencas IDEAM) | ⚪ Pendiente |
| 3 | Análisis + calibración (Butterworth, Lorenz, grid search) | ⚪ Pendiente |
| 4 | ABM en Mesa (CuencaAgent + ModeloCuencas) | ⚪ Pendiente |
| 5 | Visualización Solara tipo NetLogo | ⚪ Pendiente |
| 6 | Empaque final y publicación | ⚪ Pendiente |

---

## Fase 1 — Esqueleto del repo y documentación base

**Objetivo:** tener un repo instalable, testeable y documentable sin necesidad de datos.

- [x] Estructura de carpetas `src/` + `data/` + `docs/` + `tests/`
- [x] `pyproject.toml` con dependencias y metadatos
- [x] `requirements.txt` + `.gitignore` + `LICENSE`
- [x] Paquete `abm_enso` con subpaquetes vacíos y utilidades (`paths`, `constants`)
- [x] CLI esqueleto `abm-enso {download, calibrate, simulate, viz}`
- [x] Smoke tests con `pytest`
- [x] Configuración `mkdocs` con tema Material
- [x] Páginas índice, instalación, quickstart, roadmap, referencias

**Verificación:** `pip install -e ".[dev]"` funciona · `pytest` pasa · `mkdocs serve` renderiza.

---

## Fase 2 — Pipeline de datos

**Objetivo:** refactorizar los 4 scripts originales (`Fuente_1.py` a `Fuente_4.py`) en módulos Python parametrizados, con tests y caché.

- [ ] `data/oni.py` — descarga y parsing de ONI NOAA/CPC
- [ ] `data/era5.py` — cliente Copernicus con cache local
- [ ] `data/sirh.py` — cliente Socrata con reintentos
- [ ] `data/simma.py` — carga + limpieza del CSV SIMMA
- [ ] `data/cuencas.py` — descarga shapefile IDEAM (3-tier fallback: ArcGIS Hub → SIAC → HydroBASINS)
- [ ] Notebook `notebooks/01_exploracion_datos.ipynb`
- [ ] Implementar `abm-enso download` en el CLI
- [ ] Tests de integración con fixtures

**Verificación:** `abm-enso download` deja los 5 datasets en `data/raw/` · notebook corre limpio.

---

## Fase 3 — Análisis y calibración

**Objetivo:** obtener los parámetros $\beta_1$, $\theta$, $\kappa$ de forma reproducible contra datos, no hardcoded.

- [ ] `analysis/filtros.py` — Butterworth banda ENSO 2-7 años
- [ ] `analysis/lorenz.py` — integración + ajuste a ONI observado (cross-correlation)
- [ ] `analysis/calibracion_beta.py` — OLS por tipo de suelo
- [ ] `analysis/calibracion_theta_kappa.py` — grid search con F1-score vs SIMMA
- [ ] Notebook `notebooks/02_calibracion.ipynb`
- [ ] Implementar `abm-enso calibrate`

**Verificación:** F1 > 0.5 en período de validación 2010–2012 · parámetros guardados en `data/processed/cuencas_parametros.parquet`.

---

## Fase 4 — ABM en Mesa

**Objetivo:** implementar la simulación multi-agente y validarla contra La Niña 2010–11.

- [ ] `model/agente.py` — `CuencaAgent` (atributos heterogéneos, reglas step)
- [ ] `model/modelo.py` — `ModeloCuencas` (schedule, DataCollector)
- [ ] `model/escenarios.py` — generador de forzamientos ONI sintéticos
- [ ] Notebook `notebooks/03_simulacion.ipynb`
- [ ] Implementar `abm-enso simulate`

**Verificación:** correlación de Pearson r > 0.85 entre activaciones simuladas y catálogo SIMMA en 2010-2012.

---

## Fase 5 — Visualización Solara tipo NetLogo

**Objetivo:** app web interactiva que reproduce la experiencia NetLogo: grilla, sliders, botones play/step, series temporales sincronizadas.

- [ ] `viz/app.py` — componente Solara principal
- [ ] `viz/mapa_cuencas.py` — renderizador de la grilla espacial
- [ ] `viz/series.py` — paneles ONI + humedad + eventos
- [ ] `viz/export.py` — export a GIF con Pillow
- [ ] Implementar `abm-enso viz`

**Verificación:** app abre en navegador · controles responden · export a GIF funciona.

---

## Fase 6 — Empaque final

**Objetivo:** dejar el repo listo para publicar en GitHub.

- [ ] QA completo de código (ruff + mypy sin errores)
- [ ] Todos los notebooks corren limpio con `jupyter nbconvert --execute`
- [ ] Generar documentación estática con `mkdocs build`
- [ ] README con capturas de la simulación
- [ ] Instrucciones finales de `git init && git push`
- [ ] Tag `v0.1.0` y CHANGELOG

**Verificación:** clone limpio + quickstart funciona end-to-end sin fricción.

---

## Extensiones futuras (fuera de alcance actual)

Estas mejoras están documentadas pero no se implementarán en la versión 0.1.0:

- Modelos 2, 3 y 4 del pipeline ABM-UTADEO (opinión, red vial, decisión INVIAS)
- Resolución temporal diaria (actualmente mensual)
- Red de cuencas aguas-arriba / aguas-abajo (actualmente independientes)
- Evapotranspiración Penman-Monteith (actualmente $\kappa$ constante)
- Escenarios CMIP6 para 2050 bajo distintos RCP
