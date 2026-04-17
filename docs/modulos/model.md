# Módulo `model`

ABM de cuencas en Mesa 3.x con scheduler simultáneo.

## Arquitectura

### `CuencaAgent`

Cada cuenca es un agente con:

| Atributo | Descripción |
|----------|-------------|
| `id_cuenca` | ID HydroBASINS |
| `area_hidrografica` | Caribe / Magdalena-Cauca / Pacífico / Orinoco / Amazonas |
| `capacidad_hidrica` | C (mm), depende del área |
| `precip_climatologia` | array [12] bimodal colombiana |
| `humedad` | H(t) (mm) |
| `evento_activo` | E(t) ∈ {0, 1} |
| `beta_1` | sensibilidad ENSO (hereda del área) |
| `theta`, `kappa` | parámetros del modelo |

### Scheduler simultáneo (dos fases)

Mesa 3.x usa `AgentSet` en vez de schedulers clásicos. El modelo implementa paso simultáneo manual:

```python
# Fase A: todas calculan su próximo estado usando H(t) actual
self.agents.do("compute_next_state")

# Fase B: todas aplican el nuevo estado
self.agents.do("apply_next_state")
```

Esto garantiza que una cuenca no "ve" la actualización de sus vecinas dentro del mismo tick.

## Ecuaciones

Por cada tick $t$:

$$
P_i(t) = P_{0,i}(\text{mes}) + \beta_{1,i} \cdot \text{ONI}(t) + \varepsilon_i
$$

$$
H_i(t+1) = (1 - \kappa) \cdot H_i(t) + P_i(t+1), \quad H_i \geq 0
$$

$$
E_i(t+1) = \mathbb{1}\{H_i(t+1) > \theta \cdot C_i\}
$$

## Heterogeneidad por área

```python
BETA1_POR_AREA_DEFAULT = {
    "Magdalena-Cauca": -9.5,
    "Caribe":          -8.2,
    "Pacifico":        -5.8,
    "Orinoco":         -4.5,
    "Amazonas":        -2.0,
    "default":         -7.3,
}
```

Y capacidad hídrica por área:

```python
CAPACIDAD_POR_AREA = {
    "Pacifico":        1100,
    "Amazonas":        1200,
    "Magdalena-Cauca": 900,
    "Orinoco":         850,
    "Caribe":          750,
}
```

## Escenarios

Generadores de forzamiento ONI:

- `escenario_nina_2010(n_meses)` — gaussiana centrada, pico −1.6
- `escenario_nino_2015(n_meses)` — gaussiana centrada, pico +2.3
- `escenario_neutro(n_meses)` — ONI ≈ 0 con pequeño jitter
- `escenario_historico(inicio, fin)` — ONI NOAA real del período indicado
- `escenario_lorenz(n_meses, seed)` — ONI sintético del sistema de Lorenz

## Validación

`validacion.validar_modelo_vs_simma()` compara activaciones simuladas vs eventos SIMMA 2010–2012:

**Resultado actual:** r = 0.43, F1 = 0.74

## API

::: abm_enso.model
    options:
      show_root_heading: false
      show_source: false
