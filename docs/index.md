# ABM-ENSO-Colombia

Modelo Basado en Agentes (ABM) del sistema climático-hidrológico colombiano bajo forzamiento El Niño/Oscilación del Sur (ENSO).

## La pregunta

> **¿Puede un ABM calibrado con datos públicos reproducir el patrón espacio-temporal de activaciones hídricas en Colombia durante La Niña 2010-11?**

El evento La Niña 2010-11 produjo 3.2 millones de personas afectadas, 78 tramos viales cerrados y 29 departamentos en emergencia. Este proyecto construye el primer módulo de un pipeline ABM de cuatro etapas que busca dar respuesta cuantitativa, reproducible y abierta a esa pregunta.

## Alcance — Modelo 1 (este repo)

Este repositorio implementa **solo el Modelo 1 del pipeline ABM-UTADEO**: el módulo climático-hidrológico. Los otros tres módulos (red vial, dinámica de opinión, decisión INVIAS) quedan fuera del alcance actual y se desarrollan en repositorios independientes.

### Componentes

1. **Forzamiento externo (ENSO)** — Oscilador de Lorenz calibrado contra el índice ONI de NOAA/CPC
2. **Precipitación local** — Regresión $P(t) = P_0 + \beta_1 \cdot \text{ONI}(t)$ por tipo de suelo
3. **Balance hídrico** — $H(t+1) = (1-\kappa) \cdot H(t) + P(t+1)$
4. **Disparo de evento** — $E(t) = \mathbb{1}\{H(t) > \theta\}$

### Fuentes de datos

| Fuente | Origen | Rol en el modelo |
|---|---|---|
| ONI | NOAA/CPC | Forzamiento global, calibración de Lorenz |
| ERA5-Land | Copernicus/ECMWF | Precipitación local, humedad del suelo, escorrentía |
| SIRH | IDEAM / datos.gov.co | Nivel hidrométrico — calibración de $\kappa$ |
| SIMMA | Servicio Geológico Colombiano | Eventos confirmados — calibración de $\theta$ y validación |
| Cuencas | IDEAM (zonificación hidrográfica) | Agentes del ABM |

## Navegación

- [Instalación](instalacion.md) — cómo poner a funcionar el entorno
- [Quickstart](quickstart.md) — correr el pipeline end-to-end
- [Fundamentos del ABM](teoria/fundamentos.md) — las seis propiedades de un agente y por qué se usa ABM
- [ENSO y Lorenz](teoria/enso-lorenz.md) — por qué el ciclo ENSO se modela como sistema caótico
- [Protocolo ODD](teoria/odd.md) — especificación formal del modelo
- [Módulos](modulos/data.md) — referencia de cada subpaquete

## Estado

Este proyecto está en desarrollo activo. La fase actual y las pendientes se listan en el [roadmap](roadmap.md).
