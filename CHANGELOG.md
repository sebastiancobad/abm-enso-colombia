# Changelog

Todos los cambios notables de este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

### Heterogeneidad β₁ por área (respecto a cal. nacional -7.33):
- Magdalena-Cauca: -9.5
- Caribe: -8.2
- Pacífico: -5.8
- Orinoco: -4.5
- Amazonas: -2.0

### Verificado
- 54 tests pasando (+19 de modelo), 1 skipped
- API Mesa 3.x (AgentSet en vez de schedulers clásicos)

### Pendiente para Fase 5
- App Solara con mapa interactivo tipo NetLogo
- Controles play/pause/step, sliders θ/κ/β₁
- Export GIF/MP4

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
- `scripts/concatenar_era5.py`, `concatenar_era5_v3.py`, `generar_era5_csv.py` — utilidades para manejar chunks ZIP de Copernicus y bug de rutas con acentos en Windows

### Modificado
- `src/abm_enso/cli.py` — subcomando `abm-enso calibrate` ahora funcional
- `src/abm_enso/analysis/__init__.py` — exports públicos de los 5 módulos
- `src/abm_enso/data/era5.py` — descarga con chunking por bloques (soluciona cost limit de Copernicus)
- `src/abm_enso/data/simma.py` — encoding tolerante (utf-8-sig → utf-8 → latin-1 → cp1252)
- `scripts/download_all.py` + `src/abm_enso/cli.py` — flag `--era5-chunk-years` para configurar tamaño de request

### Verificado
- 35 tests pasando (4 smoke + 11 integración + 21 análisis); 1 skipped sin geopandas
- Pipeline end-to-end con datos reales: ONI 914 meses, ERA5 528 meses, SIMMA 6826 eventos, Cuencas 231 polígonos

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
- CSV `Resultados_SIMMA.csv` versionado en `data/raw/`
