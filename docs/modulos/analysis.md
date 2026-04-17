# Módulo `analysis`

> **Estado:** pendiente de implementación en [Fase 3](../roadmap.md#fase-3--análisis-y-calibración).

Este subpaquete contiene el análisis estadístico y la calibración de los parámetros del ABM contra datos.

## Estructura prevista

```
src/abm_enso/analysis/
├── __init__.py
├── filtros.py                  # Butterworth banda ENSO
├── lorenz.py                   # Integración + ajuste a ONI observado
├── calibracion_beta.py         # OLS ONI × ERA5 por tipo de suelo
├── calibracion_theta_kappa.py  # Grid search con F1-score
└── metricas.py                 # Pearson r, F1, KS, Moran's I
```

## API esperada

```python
from abm_enso.analysis import filtros, lorenz, calibracion_beta

# Filtro Butterworth pasa-banda ENSO
s_filt = filtros.butterworth_enso(serie_mensual, low=1/7, high=1/2, order=4)

# Generador sintético Lorenz
x_lorenz = lorenz.integrar(T=1000, dt=0.01, init=(1,1,1))
oni_sintetico = lorenz.proyectar_a_oni(x_lorenz, oni_observado)

# Calibración de β₁ por tipo de suelo
betas = calibracion_beta.ols_por_suelo(era5_precip, oni, shapefile_cuencas)

# Grid search para θ y κ
theta_opt, kappa_opt = calibracion_theta_kappa.grid_search(
    cuencas, oni, simma, theta_grid=np.arange(0.65, 0.95, 0.05)
)
```

## Ecuaciones centrales

**Butterworth banda ENSO:**

$$
H_{\text{BP}}(f) = \frac{1}{\sqrt{1 + \left(\frac{f_c}{f}\right)^{2n}}} \cdot \frac{1}{\sqrt{1 + \left(\frac{f}{f_c}\right)^{2n}}}
$$

**Lorenz system:**

$$
\begin{align}
\dot{x} &= \sigma(y-x) \\
\dot{y} &= x(\rho-z) - y \\
\dot{z} &= xy - \beta z
\end{align}
$$

**Calibración de $\beta_1$:**

$$
P'_i(t) = \alpha_i + \beta_{1,i} \cdot \text{ONI}(t) + \varepsilon
$$

donde $P'_i$ es la anomalía de precipitación (desestacionalizada) en la cuenca $i$.

**F1-score para grid search de $\theta, \kappa$:**

$$
F_1(\theta, \kappa) = \frac{2 \cdot \text{precision} \cdot \text{recall}}{\text{precision} + \text{recall}}
$$

donde precision y recall se calculan entre eventos simulados $E_i(t)$ y eventos SIMMA observados en el período 2000–2009.
