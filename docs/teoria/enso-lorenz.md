# ENSO y el oscilador de Lorenz

## El modelo de Lorenz (1963)

Edward Lorenz derivó este sistema como simplificación extrema de la convección atmosférica. A pesar de su simplicidad (3 ecuaciones ordinarias), captura la sensibilidad a condiciones iniciales que caracteriza a sistemas climáticos caóticos.

### Ecuaciones

$$
\begin{aligned}
\dot{x} &= \sigma (y - x) \\
\dot{y} &= x (\rho - z) - y \\
\dot{z} &= xy - \beta z
\end{aligned}
$$

### Parámetros canónicos

| Parámetro | Valor | Interpretación |
|-----------|------:|----------------|
| σ | 10 | Prandtl (viscosidad/difusión) |
| ρ | 28 | Rayleigh (gradiente térmico) |
| β | 8/3 | Geometría del sistema |

### Propiedades del atractor

Con ρ = 28 el sistema entra en régimen caótico y traza el famoso atractor de Lorenz (forma de mariposa) en el espacio (x, y, z). La proyección de $x(t)$ en el tiempo muestra:

- Oscilaciones cuasi-periódicas de ~0.7 unidades de tiempo
- Cambios abruptos de signo
- Amplitud acotada pero impredecible

## ¿Por qué usar Lorenz para ENSO?

El ENSO real se modela con sistemas acoplados océano-atmósfera de cientos de grados de libertad (CESM, HadGEM3, etc.). Eso es prohibitivo para un ABM académico. Lorenz es la simplificación mínima que preserva lo esencial:

### Propiedades compartidas

| Propiedad | ENSO | Lorenz |
|-----------|------|--------|
| Oscilación pseudo-periódica | ~3–7 años | ~0.7 u.t. (calibrable) |
| Amplitud acotada | ±3 °C | ±20 u.a. |
| Caos determinista | sí | sí |
| Baja predictibilidad >6m | sí | sí |

### Lo que NO comparten

- **Fase exacta** — un modelo Lorenz con misma semilla no predice cuándo ocurrirá el próximo Niño real. r(Lorenz, ONI) = 0.042.
- **Fenómenos externos** — el ENSO responde a forzantes volcánicos/antropogénicos que Lorenz ignora.

## Calibración del tiempo Lorenz → meses ONI

El sistema de Lorenz es adimensional. Para mapear $x(t)$ a una serie ONI mensual:

1. **Integrar** Lorenz durante $T = 2000$ unidades de tiempo con paso $dt = 0.01$
2. **Descartar transitorio** (primeros ~5000 pasos)
3. **Submuestrear** a N puntos (= meses de la serie ONI real)
4. **Normalizar** a media y std del ONI filtrado
5. **Alinear fase** por correlación cruzada con lag máximo de ±12 meses

```python
from abm_enso.analysis.lorenz import generar_oni_sintetico
oni_sintetico = generar_oni_sintetico(oni_filtrado, T=2000.0, seed=42)
```

## Uso en el ABM

El ONI sintético de Lorenz reemplaza al ONI observado en tres casos:

1. **Proyecciones futuras** — extender más allá de 2024
2. **Sensibilidad de corrida** — miles de Monte Carlo con distintas seeds
3. **Simulaciones > 75 años** — más allá del registro histórico (1950–presente)

Para validación y calibración, siempre usamos el ONI real de NOAA. Lorenz es un complemento, no un reemplazo.

## Referencias clave

- Lorenz, E. N. (1963). *Deterministic Nonperiodic Flow.* J. Atmos. Sci. 20:130–141.
- Jin, F.-F. (1997). *An Equatorial Ocean Recharge Paradigm for ENSO.* J. Atmos. Sci. 54:811–829.
- Timmermann, A. et al. (2018). *El Niño–Southern Oscillation complexity.* Nature 559:535–545.
