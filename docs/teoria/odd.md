# Protocolo ODD — Modelo 1

El protocolo **ODD** (*Overview, Design concepts, Details*; Grimm et al. 2020) es el estándar académico para describir modelos basados en agentes de forma reproducible y comparable.

## 1. Propósito y patrones

### 1.1 Propósito

Este modelo responde a una pregunta concreta:

> **¿Puede un ABM calibrado con datos públicos reproducir el patrón espacio-temporal de activaciones hídricas en Colombia durante La Niña 2010-11?**

El modelo NO pretende predecir eventos individuales, sino **cuantificar la distribución de riesgo hidrológico a escala nacional** bajo distintos forzamientos ENSO.

### 1.2 Patrones a reproducir

1. La distribución temporal de activaciones hídricas durante La Niña 2010-11 (SIMMA)
2. El lag de ~3 meses entre precipitación ERA5 y pico de nivel SIRH
3. La periodicidad de ~4.6 años del ciclo ENSO
4. La asimetría regional del impacto (Andes > Llanos > Caribe)

## 2. Entidades, variables de estado y escalas

### 2.1 Entidades

| Entidad | Clase Mesa |
|---|---|
| Cuenca hidrográfica | `CuencaAgent` |
| Sistema completo | `ModeloCuencas` |

### 2.2 Variables de estado

**`CuencaAgent`:**

| Variable | Tipo | Descripción |
|---|---|---|
| `id` | `int` | Identificador único |
| `tipo_suelo` | `Literal["arcilloso","arenoso","rocoso"]` | Tipo dominante |
| `beta_1` | `float` | Sensibilidad ONI→precip (mm/mes por °C) |
| `theta` | `float` | Umbral de activación (fracción de capacidad) |
| `kappa` | `float` | Tasa de drenaje mensual |
| `capacidad_hidrica` | `float` | Retención máxima (mm) |
| `humedad_acumulada` | `float` | Estado actual (mm) |
| `precip_climatologia` | `np.ndarray[12]` | $P_0$ por mes |
| `estado` | `Literal["estiaje","normal","humedo","saturado"]` | Clasificación visual |
| `eventos_historicos` | `list[int]` | Lista de ticks en que se activó |

**`ModeloCuencas`:**

| Variable | Tipo | Descripción |
|---|---|---|
| `tick` | `int` | Paso temporal actual |
| `oni_serie` | `pd.Series` | Forzamiento ONI precomputado |
| `n_cuencas` | `int` | Número de agentes |
| `schedule` | `SimultaneousActivation` | Activación síncrona |
| `datacollector` | `DataCollector` | Registro de métricas |

### 2.3 Escalas

| Dimensión | Valor |
|---|---|
| Resolución espacial | Cuenca hidrográfica (zonificación IDEAM, ~316 subzonas) |
| Resolución temporal | 1 tick = 1 mes |
| Horizonte simulado | 1981–2024 (calibración) · 60 meses (escenarios) |
| Extensión espacial | Colombia continental [−80, −5, −66, 13] |

## 3. Descripción del proceso y calendarizador

### 3.1 Orden de ejecución por tick

```
1. El modelo lee oni_serie[tick]
2. SimultaneousActivation:
   a. Cada CuencaAgent calcula P(t) = P_0 + beta_1 * ONI(t)
   b. Cada CuencaAgent actualiza H(t+1) = (1-kappa)*H(t) + P(t+1)
   c. Cada CuencaAgent evalúa E(t) = 1 si H > theta * capacidad
   d. Cada CuencaAgent actualiza su estado visual (percentiles)
3. DataCollector registra estado global
4. tick ← tick + 1
```

### 3.2 Tipo de scheduler

`SimultaneousActivation` (Mesa): todos los agentes calculan su nuevo estado antes de que cualquiera lo aplique. Elimina el sesgo de orden de activación y es adecuado porque las cuencas son independientes en v0.1.0.

## 4. Conceptos de diseño

| Concepto | Realización |
|---|---|
| **Principios básicos** | Balance hídrico simplificado + umbral de activación |
| **Emergencia** | Patrón espacial de activaciones agregadas, asimetría regional |
| **Adaptación** | No implementada en v0.1.0 |
| **Objetivos** | No aplica — agentes no optimizan |
| **Aprendizaje** | No implementado en v0.1.0 |
| **Predicción** | Agentes responden solo al estado actual, no anticipan |
| **Sensing** | Cada cuenca "ve" el ONI global y su propia humedad |
| **Interacción** | Indirecta, vía forzamiento compartido |
| **Estocasticidad** | Ruido opcional en $P(t)$ para réplicas; Lorenz es determinístico |
| **Colectivos** | Agregación por tipo de suelo y por gran cuenca |
| **Observación** | ONI, humedad media, número de activaciones por tick |

## 5. Inicialización

1. Cargar shapefile de cuencas IDEAM
2. Para cada polígono, asignar `tipo_suelo` según superposición con mapa IGAC de suelos (v0.1.0: uniforme por defecto)
3. Asignar $\beta_1$, $\theta$, $\kappa$ según `cuencas_parametros.parquet` (salida de calibración)
4. Calcular `precip_climatologia` por cuenca con ERA5 1991–2020
5. Inicializar `humedad_acumulada` con la media histórica de cada cuenca
6. Cargar el forzamiento ONI (real o sintético de Lorenz según escenario)

## 6. Input data

| Dato | Fuente | Uso |
|---|---|---|
| `oni_mensual.csv` | NOAA/CPC | Forzamiento y calibración Lorenz |
| `era5_*.nc` | Copernicus CDS | $\beta_1$ (precip) · $\kappa$ (runoff) · climatología |
| `nivel_sirh_diario.csv` | IDEAM/Socrata | Validación de lag $\kappa$ |
| `Resultados_SIMMA.csv` | SGC | Calibración $\theta$ + validación $r$ |
| `cuencas_colombia.gpkg` | IDEAM/ArcGIS Hub | Geometría espacial de los agentes |

## 7. Submodelos

### 7.1 Precipitación local

$$
P_i(t) = P_{0,i}(\text{mes}) + \beta_{1,i} \cdot \text{ONI}(t) + \varepsilon_i(t)
$$

Con $\varepsilon_i(t) \sim \mathcal{N}(0, \sigma_P)$ opcional (réplicas estocásticas).

### 7.2 Balance hídrico del suelo

$$
H_i(t+1) = (1 - \kappa_i) \cdot H_i(t) + P_i(t+1)
$$

Clip inferior en 0, sin clip superior (el sistema puede "super-saturarse").

### 7.3 Disparo de evento

$$
E_i(t) = \mathbb{1}\{ H_i(t) > \theta_i \cdot C_i \}
$$

Donde $C_i$ es la capacidad hídrica de la cuenca.

### 7.4 Estado visual

Percentiles de $H_i(t)$ respecto a su propia serie histórica:

| Estado | Rango |
|---|---|
| estiaje | $H < p_{10}$ |
| normal | $p_{10} \leq H < p_{75}$ |
| humedo | $p_{75} \leq H < p_{95}$ |
| saturado | $H \geq p_{95}$ |

## Validación

El modelo se valida contra tres métricas independientes:

| Métrica | Comparación | Criterio |
|---|---|---|
| Correlación de Pearson | Activaciones simuladas vs SIMMA (2010–2012) | $r > 0.85$ |
| F1-score | Activaciones en grilla de calibración 2000–2009 | Maximizar |
| Distribución regional | Ranking de departamentos más afectados | Top 5 debe coincidir |

## Referencias de protocolo

- Grimm, V., et al. (2020). "The ODD protocol for describing agent-based and other simulation models: A second update." *JASSS* 23(2), 7.
- Railsback, S. F., & Grimm, V. (2019). *Agent-Based and Individual-Based Modeling* (2nd ed.), Princeton University Press, cap. 3.
