# Changelog

Todos los cambios notables de este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
