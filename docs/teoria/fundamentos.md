# Fundamentos del ABM

## ¿Qué es un agente?

Un **agente** es una entidad que percibe su entorno y actúa sobre él de forma autónoma. La literatura (Macal & North 2009; Wooldridge & Jennings 1995) consensua seis propiedades operacionales:

### 1. Autónomo

Toma decisiones sin control central. Cada agente tiene su propia lógica interna; ninguna entidad superior los dirige.

### 2. Social

Interactúa con otros agentes. Las interacciones son **locales** — limitadas al vecindario o red de contactos, nunca globales.

### 3. Situado

Percibe y actúa en su entorno local. Su comportamiento depende de su posición y su contexto, no del estado global del sistema.

### 4. Adaptativo *(opcional)*

Puede modificar su comportamiento basándose en experiencias pasadas. Esta propiedad es opcional — agrega complejidad, y no todos los ABM la implementan.

### 5. Con recursos

Posee atributos que evolucionan en el tiempo (energía, capital, información, humedad acumulada). Esos recursos restringen y habilitan sus acciones.

### 6. Heterogéneo

Cada instancia puede tener atributos distintos. Esta diferencia entre agentes **no puede capturarse en una ecuación de campo medio** — es precisamente lo que motiva el uso de ABM.

## ¿Cuándo se usa ABM?

Un ABM tiene mayor costo computacional que una ecuación diferencial ordinaria (EDO). Se justifica cuando el sistema tiene al menos una de las siguientes características:

| Señal en el sistema | Por qué la EDO falla |
|---|---|
| **Atributos heterogéneos** | Las EDO promedian; pierden la varianza individual |
| **Interacción local** | Las EDO asumen mezcla perfecta |
| **Propiedades emergentes** | No se deducen de reglas micro — hay que simular |
| **Reglas adaptativas** | Las EDO no acomodan aprendizaje fácilmente |
| **Dinámica fuera de equilibrio** | Las trayectorias transitorias importan |

## ABM vs. EDO — una comparación formal

| Dimensión | EDO | Modelo Basado en Agentes |
|---|---|---|
| Ontología | Variables continuas de población | Agentes discretos individuales |
| Mezcla | Perfecta — todos con todos | Local — solo vecinos conectados |
| Heterogeneidad | Ninguna | Cada agente tiene atributos únicos |
| Equilibrio | Analítico: $dI/dt = 0$ da $I^*$ | Numérico — requiere réplicas |
| Estocasticidad | Determinístico | Estocástico — distribuye resultados |
| Convergencia | Exacta (campo medio) | ABM → EDO si agentes idénticos |

## El ciclo de ejecución

Todo ABM, independientemente de la plataforma (NetLogo, Mesa, Repast, MASON), ejecuta el mismo ciclo:

```
┌────────────┐
│ INICIALIZAR│   una sola vez, t = 0
└─────┬──────┘
      ▼
┌────────────┐
│   ACTUAR   │ ◀─────┐
│ percibir   │       │
│ decidir    │       │
│ ejecutar   │       │
└─────┬──────┘       │
      ▼              │
┌────────────┐       │
│ ACTUALIZAR │       │ t ← t + 1
│  entorno   │       │
└─────┬──────┘       │
      ▼              │
┌────────────┐       │
│  REGISTRAR │ ──────┘
│  métricas  │
└────────────┘
```

El **calendarizador (scheduler)** determina el orden de activación de los agentes y afecta directamente el resultado:

- **Activación aleatoria** — cada tick un agente distinto actúa primero. Dos corridas con misma semilla pueden dar resultados distintos si el orden cambia.
- **Activación simultánea** — todos evalúan antes de que cualquiera actúe. Tiempo discreto sincrónico.

## Aplicación al Modelo 1

En este proyecto, el agente es la **cuenca hidrográfica**, y las seis propiedades se materializan así:

| Propiedad | Realización en `CuencaAgent` |
|---|---|
| Autónomo | Cada cuenca calcula su propio $H(t+1)$ sin supervisión central |
| Social | Interacción via forzamiento ONI compartido (no hay red de cuencas en v0.1.0) |
| Situado | Atributos dependen de ubicación (tipo de suelo, climatología local) |
| Adaptativo | **No implementado** en v0.1.0 (extensión futura: aprendizaje por refuerzo) |
| Con recursos | `humedad_acumulada`, `capacidad_hidrica` |
| Heterogéneo | $\beta_1$, $\theta$, $\kappa$ varían entre cuencas según tipo de suelo |

Ver [Protocolo ODD](odd.md) para la especificación formal completa.
