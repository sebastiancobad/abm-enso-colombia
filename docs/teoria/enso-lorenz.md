# ENSO y el oscilador de Lorenz

## ¿Qué es ENSO?

El **El Niño/Southern Oscillation (ENSO)** es una oscilación acoplada océano-atmósfera en el Pacífico ecuatorial con impactos globales en precipitación y temperatura. En Colombia es el principal predictor de inundaciones (La Niña) y sequías (El Niño) en los Andes.

### Los tres estados

1. **Condiciones normales** — los vientos alisios soplan hacia el oeste; el agua caliente se acumula en el Pacífico occidental (Indonesia). El Pacífico central y oriental permanece frío. En los Andes colombianos: lluvia normal.
2. **La Niña** — vientos alisios más fuertes; el enfriamiento del Pacífico central se intensifica (SST < climatología). Más convección sobre Colombia, precipitación anómala positiva en los Andes, riesgo elevado de deslizamientos.
3. **El Niño** — vientos alisios debilitados; el Pacífico central se calienta (SST > climatología). La convección migra al este; Colombia entra en período seco, déficit hídrico en cuencas andinas, riesgo de incendios.

## El Oceanic Niño Index (ONI)

El ONI es el **índice oficial NOAA/CPC** para medir ENSO. No es temperatura absoluta — es una anomalía.

### Definición

$$
\text{ONI}(t) = \overline{\text{SST}^{\text{Niño 3.4}}(t-1, t, t+1)} - \overline{\text{SST}^{\text{clim}}_{\text{mes}(t)}}
$$

Donde:

- **Región Niño 3.4** — caja 5°N–5°S, 170°W–120°W (Pacífico ecuatorial central)
- **SST climatológica** — media mensual 1986–2015
- **Media móvil de 3 meses** — suaviza la variabilidad intraseasonal

### Clasificación

| Condición | Etiqueta |
|---|---|
| ONI ≤ −0.5 °C durante ≥ 5 meses consecutivos | La Niña |
| −0.5 < ONI < +0.5 °C | Neutro |
| ONI ≥ +0.5 °C durante ≥ 5 meses consecutivos | El Niño |

### ¿Por qué ONI y no SST directa?

La SST cruda tiene variabilidad de alta frecuencia no relacionada con ENSO. La media móvil de 3 meses del ONI elimina ese ruido y deja solo la señal ENSO. Usar SST directa sobreestimaría la duración y frecuencia de los eventos en el modelo.

## El oscilador de Lorenz como generador sintético

### El problema

El ONI histórico tiene solo ~75 años (1950-presente). Para:

1. Correr réplicas estocásticas múltiples
2. Explorar escenarios hipotéticos (La Niña más intensa, El Niño multianual)
3. Tener series continuas sin huecos

necesitamos un **generador sintético** que preserve las propiedades estadísticas del ONI real.

### El sistema de Lorenz

Edward Lorenz (1963) descubrió que el siguiente sistema de tres EDO exhibe **caos determinístico**:

$$
\begin{align}
\frac{dx}{dt} &= \sigma(y - x) \\
\frac{dy}{dt} &= x(\rho - z) - y \\
\frac{dz}{dt} &= xy - \beta z
\end{align}
$$

Con parámetros canónicos $\sigma = 10$, $\rho = 28$, $\beta = 8/3$, el sistema produce el **atractor de Lorenz** — una trayectoria limitada, pseudo-periódica, sin repetirse jamás.

### ¿Por qué Lorenz para ENSO?

Porque el ENSO real tiene exactamente estas propiedades:

- **Pseudo-periodicidad** — el ciclo real oscila con período ≈ 4.6 años pero no es exactamente periódico
- **Sensibilidad a condiciones iniciales** — dos estados atmosféricos casi idénticos divergen en meses
- **Bimodalidad** — el sistema tiende a quedarse largos períodos cerca de uno de dos "lóbulos" (análogos a regímenes El Niño / La Niña)
- **Estacionaridad estadística** — la distribución de amplitudes es estable en el largo plazo

### Proyección X(t) → ONI sintético

El procedimiento es:

1. Integrar el sistema con condiciones iniciales $(x_0, y_0, z_0) = (1, 1, 1)$ hasta $t = T$ usando `scipy.integrate.odeint`.
2. Normalizar la variable $x(t)$ a la media y desviación estándar del ONI observado filtrado con Butterworth.
3. Calibrar el desfase temporal por correlación cruzada máxima.

$$
\text{ONI}_{\text{Lorenz}}(t) = \mu_{\text{ONI}} + \sigma_{\text{ONI}} \cdot \frac{x(t) - \overline{x}}{\sigma_x}
$$

El resultado tiene la misma estructura espectral (período ≈ 4.6 años), pero es continuo, sin huecos, y preserva la sensibilidad a condiciones iniciales del ENSO.

## El filtro Butterworth pasa-banda

Antes de ajustar Lorenz al ONI observado, filtramos la banda ENSO para eliminar:

- **Alta frecuencia** — variabilidad intraseasonal, ruido diario
- **Baja frecuencia** — tendencia climática de largo plazo (cambio climático)

### Parámetros

| Parámetro | Valor | Justificación |
|---|---|---|
| Orden | 4 | Balance entre rolloff y estabilidad numérica |
| Banda pasa | 2–7 años | Rango físico del ENSO |
| Aplicación | `filtfilt` (fase cero) | No introduce desfase temporal |

### Aplicación a las 4 fuentes

| Fuente | Pre-proceso antes del filtro | Serie filtrada |
|---|---|---|
| F1 · ONI | Ninguno (ya tiene MA-3) | `oni_enso(t)` |
| F2 · ERA5 (3 vars) | Restar climatología mensual | `precip_enso`, `soil_enso`, `runoff_enso` |
| F3 · SIRH | Agregar a mensual + quitar clima + interpolar gaps ≤ 3M | `nivel_enso` por estación |
| F4 · SIMMA | Conteo mensual + $\sqrt{\cdot}$ + clima + filtrar 2000–2023 | `eventos_enso(t)` |

## Relación con el ABM

En el `ModeloCuencas`, la variable ONI entra como **forzamiento externo global** compartido por todos los agentes. Cada cuenca responde según sus propios parámetros:

$$
P_i(t) = P_{0,i} + \beta_{1,i} \cdot \text{ONI}(t)
$$

Donde $i$ indexa la cuenca y los subíndices en $\beta_{1,i}$ y $P_{0,i}$ reflejan la heterogeneidad entre cuencas (tipo de suelo, climatología local).
