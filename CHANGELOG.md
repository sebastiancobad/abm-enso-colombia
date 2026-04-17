# Changelog

Todos los cambios notables de este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — Fase 6 · Release estable

### Agregado
- `README.md` completo con badges (versión, licencia, Python, tests, Mesa), sección de resultados calibrados, quickstart, estructura del proyecto, comandos CLI documentados, referencias académicas y guía de citación
- `CITATION.cff` para citación académica formal (formato Citation File Format 1.2.0) con referencias a Lorenz 1963 y Poveda 2004
- `docs/index.md`, `docs/quickstart.md`, `docs/instalacion.md` — documentación completa navegable con mkdocs
- `docs/teoria/{fundamentos,enso-lorenz,odd}.md` — fundamentos físicos, sistema de Lorenz y descripción ODD del modelo
- `docs/modulos/{data,analysis,model,viz}.md` — documentación por subpaquete con ejemplos de uso
- `docs/referencias.md` — bibliografía completa
- `docs/roadmap.md` — estado del proyecto y trabajo futuro

### Consolidado
- Pipeline end-to-end validado con datos reales: ONI 914 meses, ERA5 528 meses, SIMMA 6826 eventos, Cuencas 231 polígonos
- 70 tests pasando (4 smoke + 11 data + 21 analysis + 19 model + 15 viz)
- App Solara corriendo con mapa de 231 cuencas + panel de estado + series temporales Plotly + heatmap + periodograma
- Calibración confirmada: β₁ = −7.33 mm/mes/°C, θ* = 0.700, κ* = 0.275, F1 = 0.629 (vs 6826 eventos SIMMA)

### Estable desde esta versión
- API pública de `abm_enso.{data, analysis, model, viz}`
- Formato de `data/processed/cuencas_parametros.parquet`
- Esquema de argumentos del CLI `abm-enso {download,calibrate,simulate,viz}`

---

## [0.5.0] — Fase 5 · Visualización Solara tipo NetLogo

### Agregado
- `src/abm_enso/viz/app.py` — layout Solara principal con autoplay threading y callbacks reactivos
- `src/abm_enso/viz/simulacion.py` — `SimulacionEnVivo`: wrapper de `ModeloCuencas` con API simplificada para la UI (reset_con_escenario, step, snapshots)
- `src/abm_enso/viz/estado.py` — variables reactivas compartidas entre componentes
- `src/abm_enso/viz/mapa_cuencas.py` — choropleth matplotlib con 4 colores por estado hídrico (estiaje/normal/humedo/saturado), renderiza las 231 cuencas HydroBASINS
- `src/abm_enso/viz/series.py` — panel Plotly con 4 subplots sincronizados (ONI, % activadas, humedad media, eventos SIMMA si escenario histórico)
- `src/abm_enso/viz/heatmap.py` — mapa de calor Plotly cuencas × tiempo (top 80 por activaciones, ordenado por área hidrográfica)
- `src/abm_enso/viz/periodograma.py` — Lomb-Scargle con banda ENSO sombreada (2-7 años) y marcador del pico dominante
- `src/abm_enso/viz/controles.py` — panel lateral tipo NetLogo: play/pause/step/reset + sliders θ/κ/ruido/seed + selector escenario + exports
- `src/abm_enso/viz/export.py` — grabación a GIF (imageio) y MP4 (imageio-ffmpeg) con detección automática de disponibilidad
- `tests/test_viz.py` — 15 tests: lógica pura de SimulacionEnVivo + render helpers + export detection

### Modificado
- `src/abm_enso/cli.py` — subcomando `abm-enso viz` ahora lanza `solara run` (antes Dash, descontinuado)
- `pyproject.toml` + `environment.yml` — añadidas `imageio>=2.34` y `imageio-ffmpeg>=0.4`

### Verificado
- 70 tests pasando (4 smoke + 11 data + 21 analysis + 19 model + 15 viz)
- App Solara arranca con `abm-enso viz` o `solara run src/abm_enso/viz/app.py`
- Autoplay en thread separado con velocidad configurable 1-10 ticks/seg
- Exports guardan en `outputs/simulacion_{escenario}_{timestamp}.{gif|mp4}`

### Pendiente para Fase 6
- mkdocs build con screenshots de la app
- Badge de versión + CI en GitHub Actions
- Release v1.0.0 en GitHub

---

## [0.4.0] — Fase 4 · ABM en Mesa

### Agregado
- `src/abm_enso/model/agente.py` — `CuencaAgent` con scheduler simultáneo (compute/apply en dos fases)
- `src/abm_enso/model/modelo.py` — `ModeloCuencas` con β₁ por área hidrográfica, ruido estocástico opcional, reproducibilidad vía seed
- `src/abm_enso/model/escenarios.py` — generadores de forzamiento ONI: nina-2010, nino-2015, neutro, historico, lorenz, custom
- `src/abm_enso/model/validacion.py` — métricas r/RMSE/F1 contra SIMMA 2010-2012
- `src/abm_enso/pipeline.py` — función `simular_escenario()`
- `src/abm_enso/cli.py` — subcomando `abm-enso simulate` funcional con flags `--scenario`, `--meses`, `--replicas`, `--ruido`, `--seed`, `--validar`
- `notebooks/03_simulacion.ipynb` — comparación Niña vs Niño vs neutro + Monte Carlo con 30 réplicas + validación SIMMA
- `tests/test_model.py` — 19 tests con síntesis en runtime

### Heterogeneidad β₁ por área
- Magdalena-Cauca: -9.5
- Caribe: -8.2
- Pacífico: -5.8
- Orinoco: -4.5
- Amazonas: -2.0

### Verificado
- 54 tests pasando (+19 de modelo), 1 skipped
- API Mesa 3.x (AgentSet en vez de schedulers clásicos)

---

## [0.3.0] — Fase 3 · Análisis y calibración

### Agregado
- `src/abm_enso/analysis/filtros.py` — Butterworth pasa-banda ENSO (2-7 años) + desestacionalización mensual
- `src/abm_enso/analysis/lorenz.py` — integrador RK4 del sistema de Lorenz + proyección a ONI con cross-correlation fit
- `src/abm_enso/analysis/metricas.py` — Pearson r, F1-score, RMSE, periodograma Lomb-Scargle
- `src/abm_enso/analysis/calibracion_beta.py` — OLS ONI × ERA5 precipitación por grupo de cuencas
- `src/abm_enso/analysis/calibracion_theta_kappa.py` — grid search F1 contra eventos SIMMA
- `src/abm_enso/pipeline.py` — función `calibrar_modelo()` end-to-end que guarda `data/processed/cuencas_parametros.parquet`
- `notebooks/02_calibracion.ipynb` — pipeline completo con panel interactivo Plotly de sensibilidad θ vs κ
- `tests/test_analysis.py` — 21 tests con datos sintéticos en runtime (sin archivos fixture)

### Modificado
- `src/abm_enso/cli.py` — subcomando `abm-enso calibrate` ahora funcional
- `src/abm_enso/analysis/__init__.py` — exports públicos de los 5 módulos

### Verificado
- 35 tests pasando (4 smoke + 11 integración + 21 análisis); 1 skipped sin geopandas
- Pipeline end-to-end probado con datos sintéticos en runtime
- `abm-enso calibrate` ejecuta el flujo Butterworth → Lorenz → OLS → grid search y guarda `data/processed/cuencas_parametros.parquet`

### Pendiente para Fase 4
- ABM en Mesa (CuencaAgent + ModeloCuencas)
- Simulación en escenarios ENSO
- Validación r vs SIMMA 2010-2012

---

## [0.2.0] — Fase 2 · Pipeline de datos

### Agregado
- `src/abm_enso/pipeline.py` — orquestador `descargar_todas()` importable
- `src/abm_enso/data/oni.py` — cliente NOAA/CPC con parser robusto y cache local
- `src/abm_enso/data/era5.py` — cliente Copernicus CDS con modo `daily` → agregación mensual automática
- `src/abm_enso/data/sirh.py` — cliente Socrata (datos.gov.co) con bloques anuales y reintentos
- `src/abm_enso/data/simma.py` — estrategia híbrida: descarga SGC oficial → fallback al CSV local versionado
- `src/abm_enso/data/cuencas.py` — descarga IDEAM con fallback 3-tier (ArcGIS Hub → HydroBASINS)
- `notebooks/01_exploracion_datos.ipynb` — 6 secciones exploratorias con las 5 fuentes
- `tests/test_data_integration.py` — 11 tests de integración con fixtures mock (sin llamadas a red real)
- `environment.yml` — instalación conda-forge recomendada (soluciona problemas GDAL en Windows)
- `scripts/download_all.py` — ahora funcional, thin wrapper sobre `pipeline.descargar_todas()`

### Modificado
- `src/abm_enso/cli.py` — subcomando `download` ahora funcional con flags `--solo`, `--force`, `--era5-mode`, `--skip-on-error`
- `src/abm_enso/data/__init__.py` — exporta los 5 submódulos públicamente
- `docs/instalacion.md` — documenta `environment.yml` como método recomendado

### Verificado
- 15 tests pasando (4 smoke + 11 integración); 1 skipped si geopandas no está instalado
- Todos los módulos usan rutas dinámicas (`_paths.X`) para permitir testing con fixtures

### Fases pendientes
- Fase 3: Análisis + calibración (Butterworth, Lorenz, grid search θ/κ)
- Fase 4: ABM en Mesa (`CuencaAgent` + `ModeloCuencas`)
- Fase 5: Visualización Solara tipo NetLogo
- Fase 6: Empaque final y publicación v1.0.0

---

## [0.1.0] — Fase 1 · Esqueleto del repo

### Agregado
- Estructura de carpetas `src/` + `data/` + `docs/` + `tests/` + `scripts/` + `outputs/`
- `pyproject.toml` con dependencias pinned y configuración de ruff/mypy/pytest
- `requirements.txt` para instalación rápida sin modo desarrollo
- `LICENSE` (MIT) y `.gitignore` exhaustivo
- Paquete `abm_enso` con subpaquetes esqueleto (`data`, `analysis`, `model`, `viz`, `utils`)
- `utils/paths.py` — rutas canónicas auto-resueltas desde la raíz del repo
- `utils/constants.py` — constantes físicas, bbox Colombia, umbrales ENSO, tipos de suelo, parámetros Lorenz canónicos
- CLI `abm-enso` con subcomandos `download`, `calibrate`, `simulate`, `viz` (esqueletos)
- `tests/test_smoke.py` — 4 tests de integridad estructural
- Configuración `mkdocs.yml` con tema Material, español, MathJax
- Documentación base: `index`, `instalacion`, `quickstart`, `roadmap`, `referencias`
- Teoría: `teoria/fundamentos.md`, `teoria/enso-lorenz.md`, `teoria/odd.md`
- Placeholders de módulos: `modulos/{data,analysis,model,viz}.md`
- CSV `Resultados_SIMMA.csv` versionado en `data/raw/`## [0.5.0] - Fase 5 - Visualizacion interactiva Dash

### Agregado
- src/abm_enso/viz/app.py - app Dash con layout estilo NetLogo: controles laterales, mapa central, series derechas
- src/abm_enso/viz/mapa.py - choropleth de Colombia con estado hidrico por cuenca (4 colores discretos)
- src/abm_enso/viz/series.py - 3 plots sincronizados (ONI, humedad, activaciones + SIMMA overlay)
- src/abm_enso/viz/export.py - generador de GIF programatico via kaleido + imageio
- src/abm_enso/viz/estilos.py - design tokens (paleta, tipografia)
- src/abm_enso/cli.py - subcomando abm-enso viz con flags --host, --port, --debug
- notebooks/04_demo_viz.ipynb - demo interactivo + export GIF
- tests/test_viz.py - 6 smoke tests sin levantar servidor

### Caracteristicas del visualizador
- Dropdown de escenario: historico, nina-2010, nino-2015, neutro, lorenz
- Sliders theta, kappa, ruido con defaults calibrados
- Controles Play/Pause/Step/Reset + slider FPS
- Slider de tick manual para navegar el tiempo
- Mapa se actualiza tick-a-tick con la distribucion espacial del estado
- Series temporales con linea vertical marcando el tick actual
- SIMMA observado se superpone automaticamente en escenario historico

### Verificado
- 56 tests pasando (54 + 2 viz); aplicacion construye sin errores

---


