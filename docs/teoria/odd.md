# Descripción ODD del modelo

Formato estándar para documentar ABMs (Grimm et al. 2006, 2020).

## 1. Objetivo (Overview)

### Propósito

Cuantificar el impacto del ENSO sobre la dinámica hidrológica de las cuencas colombianas para predecir la probabilidad de activación de movimientos en masa (deslizamientos, flujos, caídas).

### Entidades, variables de estado, escalas

**Agentes:** 231 cuencas HydroBASINS nivel 6 recortadas a Colombia.

**Variables de estado por cuenca:**

| Variable | Tipo | Unidad |
|----------|------|--------|
| `id_cuenca` | string | — |
| `area_hidrografica` | categoría (5) | — |
| `capacidad_hidrica` | float | mm |
| `precip_climatologia[12]` | array | mm/mes |
| `humedad` | float | mm |
| `evento_activo` | bool | — |
| `beta_1` | float | mm/mes/°C |
| `theta`, `kappa` | float | fracción |

**Variables globales:**

- `oni_actual` (float °C)
- `tick` (int meses desde inicio)

**Escalas:**

- Espacial: subcuencas HydroBASINS nivel 6 (~1000–10000 km² cada una)
- Temporal: pasos mensuales, simulaciones típicas 36–240 meses

### Visión general del proceso y scheduling

En cada tick $t$:

1. Actualizar `oni_actual` desde la serie de forzamiento
2. **Fase A:** cada cuenca lee su $H(t)$ y calcula $H(t+1)$, $E(t+1)$
3. **Fase B:** cada cuenca aplica $H(t+1)$ y registra historial
4. Recolectar métricas agregadas

El scheduler es simultáneo — ninguna cuenca ve la actualización de otra dentro del mismo tick.

## 2. Conceptos de diseño (Design Concepts)

### Principios básicos

Balance hídrico con memoria + umbral no lineal para evento.

### Emergencia

La correlación espacio-temporal entre activaciones de cuencas del mismo área hidrográfica **no** está programada explícitamente — emerge del forzamiento común ONI y los parámetros heterogéneos por área.

### Adaptación

Los agentes no adaptan su comportamiento en v1.0. Fase 7+ podría incorporar aprendizaje (por ejemplo, cuencas "aprendiendo" su θ óptimo).

### Objetivos

Los agentes no tienen objetivos individuales; siguen ecuaciones deterministas + ruido.

### Aprendizaje / predicción / sensing

No aplica en v1.0.

### Interacción

Ninguna en el Modelo 1. Los otros 3 modelos de la arquitectura UTADEO añaden interacciones vía opinión pública, red vial e intervenciones INVIAS.

### Estocasticidad

Controlada por `ruido_precip`:

$$
P_i(t) = P_{0,i}(\text{mes}) + \beta_{1,i} \cdot \text{ONI}(t) + \varepsilon_i, \quad \varepsilon_i \sim \mathcal{N}(0, \sigma_P^2)
$$

Con `ruido_precip = 0`, la corrida es totalmente determinista dado el seed.

### Colectividades

Las cuencas se agrupan por `area_hidrografica`. Comparten $\beta_1$ dentro del grupo.

### Observación

Por cada tick se registra:

- `n_activaciones` (count)
- `humedad_media` (mm)
- `oni` (°C)

Al final: matriz de activaciones cuenca × tiempo para análisis espacio-temporal.

## 3. Detalles (Details)

### Inicialización

- Cada cuenca inicia con $H_0 = 0$
- `oni_actual` se toma del primer valor de `oni_serie`
- `random.seed(seed)` garantiza reproducibilidad

### Input data

- `oni_serie` — pd.Series con el forzamiento ONI mensual (puede ser real, Lorenz sintético o escenario idealizado)
- `gdf_cuencas` — GeoDataFrame con las geometrías y atributos iniciales

### Submodelos

**P1 — Balance de precipitación:**

$$
P_i(t+1) = P_{0,i}(\text{mes}(t+1)) + \beta_{1,i} \cdot \text{ONI}(t+1) + \varepsilon_i
$$

**P2 — Balance hídrico:**

$$
H_i(t+1) = \max(0,\; (1 - \kappa) \cdot H_i(t) + P_i(t+1))
$$

**P3 — Activación de evento:**

$$
E_i(t+1) = \mathbb{1}\{H_i(t+1) > \theta \cdot C_i\}
$$

## Calibración de parámetros

| Parámetro | Método | Valor |
|-----------|--------|------:|
| $\beta_1$ por área | OLS agregado | −9.5 a −2.0 |
| $\theta^*$ | Grid search F1 vs SIMMA | 0.700 |
| $\kappa^*$ | Grid search F1 vs SIMMA | 0.275 |
| $C_i$ por área | Literatura + ajuste | 750–1200 mm |
| $\sigma_P$ | Libre (UI) | 0–30 mm |

## Validación

### F1 calibración

0.629 sobre 528 meses de ERA5 con 6826 eventos SIMMA.

### Validación out-of-sample

Con $\theta^*, \kappa^*$ calibrados sobre todo el período, evaluar 2010–2012:
**r = 0.43, F1 = 0.74**

## Referencias

- Grimm, V. et al. (2020). *The ODD Protocol for Describing Agent-Based and Other Simulation Models.* JASSS 23(2):7.
- Railsback, S. F. & Grimm, V. (2019). *Agent-Based and Individual-Based Modeling.* Princeton UP, 2nd ed.
