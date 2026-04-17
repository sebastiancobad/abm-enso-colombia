"""Estado reactivo compartido entre componentes Solara.

Todas las piezas de la UI (mapa, series, controles) escuchan los mismos
``solara.Reactive`` — al cambiar uno, todo se re-renderiza.

No hay singleton de la simulación aquí: ese objeto se guarda como atributo
del ``App`` en ``app.py`` vía ``solara.use_state`` o ``solara.reactive``.
"""

from __future__ import annotations

import solara

# --------- Configuración de la corrida ---------
escenario = solara.reactive("historico")             # str: "historico" | "nina-2010" | ...
n_meses = solara.reactive(120)                        # meses de simulación
theta = solara.reactive(0.78)
kappa = solara.reactive(0.22)
ruido = solara.reactive(0.0)
seed = solara.reactive(42)

# --------- Control de play/pause/velocidad ---------
jugando = solara.reactive(False)                      # play/pause
velocidad_tps = solara.reactive(2)                    # ticks por segundo
tick_actual = solara.reactive(0)                      # avanza para triggear re-render

# --------- Revisión estética ---------
mostrar_simma = solara.reactive(True)                 # superponer SIMMA en serie
paleta = solara.reactive("viridis")                    # esquema de color del mapa

# --------- Estado puro de la UI (no semantically-reactive) ---------
ultimo_export = solara.reactive("")                   # mensaje tipo "GIF guardado en..."


OPCIONES_ESCENARIO = [
    ("historico",  "Histórico (ONI real 1981-2024)"),
    ("nina-2010",  "La Niña 2010-2011"),
    ("nino-2015",  "El Niño 2015-2016"),
    ("neutro",     "Neutro constante"),
    ("lorenz",     "Lorenz sintético"),
]
