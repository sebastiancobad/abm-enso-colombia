# Fundamentos teóricos

## El Niño Southern Oscillation (ENSO)

El ENSO es la principal fuente de variabilidad climática interanual en el trópico. Se caracteriza por oscilaciones en la temperatura superficial del Pacífico ecuatorial entre tres fases:

- **El Niño** — fase cálida (ONI > +0.5 °C)
- **La Niña** — fase fría (ONI < −0.5 °C)
- **Neutro** — entre ambos

En Colombia, la respuesta hidroclimática es **anticorrelacionada** al ONI:

| Fase | Efecto en Colombia |
|------|--------------------|
| El Niño | Sequía, déficit de lluvia, riesgo de incendios |
| La Niña | Excesos de lluvia, inundaciones, remociones en masa |

Esta anticorrelación aparece como $\beta_1 < 0$ en la ecuación del modelo (−7.33 mm/mes/°C ONI a escala nacional).

## Oscilador de Lorenz como proxy ENSO

Aunque el ENSO real se modela con sistemas acoplados océano-atmósfera (ZC, Jin-Timmermann, etc.), el sistema de Lorenz (1963) captura las propiedades estadísticas esenciales:

- Pseudo-periodicidad (~4.6 años tras calibración)
- Sensibilidad a condiciones iniciales
- Régimen caótico determinista
- Estacionariedad estadística

Esto permite generar series ONI sintéticas infinitamente largas para proyecciones y análisis de sensibilidad, algo que no se puede hacer con los datos observados (limitados a 1950–presente).

## Modelos basados en agentes (ABM)

Un ABM representa un sistema como un conjunto de entidades (agentes) autónomas que interactúan en cada paso temporal. En este modelo:

- **Agente:** cada cuenca hidrográfica (N = 231)
- **Entorno:** serie temporal ONI común a todas
- **Tiempo:** pasos mensuales
- **Regla local:** ecuación de balance hídrico + umbral de activación
- **Interacción:** ninguna inter-agente (Modelo 1 puro clima)

**Ventajas sobre una regresión directa:**

1. Heterogeneidad explícita por área hidrográfica
2. Memoria (H(t) persiste tick a tick)
3. No-linealidad del umbral (evento = sí/no, no gradiente)
4. Reproducibilidad con `seed` + posibilidad de Monte Carlo con ruido

## Scheduler simultáneo

Mesa 3.x descartó los schedulers clásicos (`SimultaneousActivation`). El scheduler simultáneo se implementa manualmente:

```python
# Dos fases dentro del mismo step():
self.agents.do("compute_next_state")  # todos leen H(t), calculan H(t+1)
self.agents.do("apply_next_state")     # todos escriben H(t+1)
```

Esto es crítico cuando se introducen interacciones entre agentes (Fases futuras), porque garantiza que una cuenca no "ve" el estado ya actualizado de sus vecinas dentro del mismo tick.

## Validación

El modelo se valida contra dos fuentes:

### SIMMA (Servicio Geológico Colombiano)

Sistema de Información de Movimientos en Masa — 6826 eventos de deslizamientos, flujos y caídas documentados entre 1981 y 2024. Usamos la tasa mensual como ground truth binario: mes con evento = mes con ≥5 reportes SIMMA.

**Resultado:** F1 = 0.629 sobre los 528 meses de datos ERA5.

### Validación independiente 2010-2012

Período de La Niña extrema. El modelo reproduce la escalada de activaciones en 2011 con r = 0.43 y F1 = 0.74.

## Limitaciones

- **$r^2$ modesto (0.176) del OLS global** — promediar Colombia entera mezcla regiones con respuestas opuestas. La heterogeneidad por área mitiga parcialmente esto.
- **Sin dinámica de suelos** — κ es un parámetro global, no depende del tipo de suelo (arcilloso vs arenoso). Mejorable con mapa IGAC 1:100k.
- **Sin precipitación granular** — P(t) se modela con climatología + anomalía por ONI, no con precipitación observada por cuenca. Mejora futura: reemplazar ERA5 nacional por CHIRPS 0.05° por cuenca.
- **Lorenz no imita en fase** — r(Lorenz, ONI) = 0.042. El atractor **sustituye** el forzamiento, no lo predice.
