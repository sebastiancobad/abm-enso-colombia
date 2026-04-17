# Changelog

Todos los cambios notables de este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fase 1 (actual) — Esqueleto del repo

#### Agregado
- Estructura de carpetas `src/` + `data/` + `docs/` + `tests/` + `scripts/` + `outputs/`
- `pyproject.toml` con dependencias pinned y configuración de ruff/mypy/pytest
- `requirements.txt` redundante para instalación rápida sin modo desarrollo
- `LICENSE` (MIT) y `.gitignore` exhaustivo
- Paquete `abm_enso` con subpaquetes esqueleto (`data`, `analysis`, `model`, `viz`, `utils`)
- `utils/paths.py` — rutas canónicas auto-resueltas desde la raíz del repo
- `utils/constants.py` — constantes físicas, bbox Colombia, umbrales ENSO, tipos de suelo, parámetros Lorenz canónicos
- CLI `abm-enso` con subcomandos `download`, `calibrate`, `simulate`, `viz` (esqueletos)
- `tests/test_smoke.py` — 4 tests de integridad estructural (todos pasan ✅)
- Configuración `mkdocs.yml` con tema Material, español, MathJax
- Documentación base: `index`, `instalacion`, `quickstart`, `roadmap`, `referencias`
- Teoría: `teoria/fundamentos.md`, `teoria/enso-lorenz.md`, `teoria/odd.md`
- Placeholders de módulos: `modulos/{data,analysis,model,viz}.md`
- CSV `Resultados_SIMMA.csv` versionado en `data/raw/`

#### Fases pendientes
- Fase 2: Pipeline de datos (ONI, ERA5, SIRH, SIMMA, cuencas IDEAM)
- Fase 3: Análisis + calibración (Butterworth, Lorenz, grid search)
- Fase 4: ABM en Mesa (`CuencaAgent` + `ModeloCuencas`)
- Fase 5: Visualización Solara tipo NetLogo
- Fase 6: Empaque final y publicación v0.1.0
