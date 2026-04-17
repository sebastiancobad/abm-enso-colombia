# Módulo `model`

> **Estado:** pendiente de implementación en [Fase 4](../roadmap.md#fase-4--abm-en-mesa).

Este subpaquete implementa el modelo basado en agentes en Mesa. La especificación formal está en el [Protocolo ODD](../teoria/odd.md).

## Estructura prevista

```
src/abm_enso/model/
├── __init__.py
├── agente.py        # CuencaAgent
├── modelo.py        # ModeloCuencas
└── escenarios.py    # Generadores de forzamientos ONI
```

## API esperada

```python
from abm_enso.model import ModeloCuencas

# Instanciar con parámetros calibrados
modelo = ModeloCuencas(
    gdf_cuencas=cuencas,
    oni_serie=oni_lorenz,
    beta1_por_suelo={"arcilloso": 1.82, "arenoso": 1.31, "rocoso": 0.94},
    theta=0.78,
    kappa=0.22,
    seed=42,
)

# Correr simulación
for _ in range(60):
    modelo.step()

# Extraer resultados
df_resultados = modelo.datacollector.get_model_vars_dataframe()
df_agentes = modelo.datacollector.get_agent_vars_dataframe()
```

## Clase `CuencaAgent`

Atributos principales:

```python
class CuencaAgent(mesa.Agent):
    unique_id: int
    tipo_suelo: Literal["arcilloso", "arenoso", "rocoso"]
    beta_1: float
    theta: float
    kappa: float
    capacidad_hidrica: float
    humedad_acumulada: float
    precip_climatologia: np.ndarray  # [12]
    estado: Literal["estiaje", "normal", "humedo", "saturado"]
    eventos_historicos: list[int]
```

Método `step()`:

1. Leer `self.model.oni_actual`
2. Calcular $P(t) = P_0[\text{mes}] + \beta_1 \cdot \text{ONI}(t)$
3. Actualizar $H(t+1) = (1-\kappa) \cdot H(t) + P(t+1)$
4. Evaluar $E(t) = \mathbb{1}\{H(t) > \theta \cdot C\}$
5. Actualizar estado visual

## Clase `ModeloCuencas`

Configuración:

```python
class ModeloCuencas(mesa.Model):
    def __init__(
        self,
        gdf_cuencas: gpd.GeoDataFrame,
        oni_serie: pd.Series,
        beta1_por_suelo: dict[str, float],
        theta: float,
        kappa: float,
        seed: int = 42,
    ): ...
```

Scheduler: `SimultaneousActivation`.

DataCollector recolecta por tick:

- `oni` — forzamiento actual
- `humedad_media` — promedio global
- `n_activaciones` — número de cuencas con $E=1$
- `n_saturadas` — número de cuencas en estado "saturado"
- Por agente: `humedad`, `estado`, `evento`

## Validación contra La Niña 2010-11

El notebook `03_simulacion.ipynb` corre:

1. Simulación con forzamiento ONI real 2009–2012
2. Comparación contra catálogo SIMMA (conteo mensual de eventos)
3. Reporte de Pearson $r$, RMSE del timing, distribución regional
4. Objetivo: $r > 0.85$
