# Roadmap

## Estado actual: v1.0.0 ✅

Todas las 6 fases del plan original completadas.

### Fase 1 — Esqueleto del repo (v0.1.0)
- Estructura `src/` + `data/` + `docs/` + `tests/`
- `pyproject.toml` con setuptools + ruff/mypy/pytest
- CLI esqueleto con 4 subcomandos
- 4 smoke tests

### Fase 2 — Pipeline de datos (v0.2.0)
- 5 clientes de datos: ONI, ERA5, SIRH, SIMMA, Cuencas
- Estrategia 3-tier con fallback para cuencas
- Chunking de ERA5 para evitar cost limit de Copernicus
- 11 tests de integración con mocks

### Fase 3 — Análisis y calibración (v0.3.0)
- Butterworth pasa-banda 2–7 años
- Oscilador de Lorenz + cross-correlation fit
- OLS ONI × ERA5 por grupo
- Grid search θ/κ con F1 contra SIMMA
- 21 tests con síntesis en runtime

### Fase 4 — ABM en Mesa (v0.4.0)
- `CuencaAgent` con scheduler simultáneo
- `ModeloCuencas` con heterogeneidad por área
- 6 escenarios ENSO generadores
- Validación r=0.43, F1=0.74 vs SIMMA 2010-2012
- 19 tests del modelo

### Fase 5 — Visualización Solara tipo NetLogo (v0.5.0)
- App Solara con 6 componentes: mapa + series + heatmap + periodograma + controles + dashboard
- Export GIF/MP4 con imageio
- 15 tests de la UI
- **Total: 70 tests pasando**

### Fase 6 — Empaque final (v1.0.0)
- README completo con badges y resultados
- mkdocs desplegado en GitHub Pages
- CI en GitHub Actions (tests + docs)
- CITATION.cff
- Release v1.0.0 en GitHub

## Pendiente para v1.1+

### Mejoras de visualización

- [ ] Modo fluido Plotly choropleth (animación en navegador)
- [ ] Modo reducido con 5 regiones hidrográficas agregadas
- [ ] Export PNG del mapa individual por frame
- [ ] Tooltip con datos al hover sobre cuenca

### Calibración refinada

- [ ] β₁ por cuenca individual usando CHIRPS 0.05°
- [ ] κ heterogéneo según tipo de suelo (IGAC 1:100k)
- [ ] Validación cruzada 5-fold temporal
- [ ] Análisis de sensibilidad Morris / Sobol

### Extensiones del ABM

- [ ] Interacción inter-agente vía topología de drenaje (cuencas aguas abajo)
- [ ] Evapotranspiración como función de temperatura ERA5
- [ ] Persistencia multi-escala (anomalía decadal tipo PDO)

### Modelos acoplados (Fases 7+)

Los otros 3 modelos de la arquitectura ABM-UTADEO:

- Modelo 2 — opinión pública sobre infraestructura
- Modelo 3 — red vial y conectividad
- Modelo 4 — intervenciones INVIAS

Cada uno vive en su propio repo; este repo es el Modelo 1 auto-contenido.
