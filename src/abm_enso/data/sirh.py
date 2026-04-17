"""Nivel hidrométrico SIRH-IDEAM vía API Socrata.

Refactor de `Fuente_3.py` con reintentos, bloques anuales y logging.

La API de `datos.gov.co` usa Socrata. El dataset de niveles es `vfth-yucv`
("Datos Hidrometeorológicos Crudos"). No requiere API key para consultas
ligeras, pero conviene pedir una gratis en
https://evergreen.data.socrata.com/signup para mayor rate limit.

Las 3 estaciones por defecto cubren tres cuencas andinas distintas:

- Culima (0035077180)  — Orinoquía-Boyacá, cap. moderada
- Río Claro (0026157190) — Cauca-Caldas, alta pendiente
- La Mora (0021167080) — Alto Magdalena-Tolima

Tarda ~20 min para 3 estaciones × 10 años con bloques anuales.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Final

import pandas as pd

from abm_enso.utils import paths as _paths
from abm_enso.utils.paths import ensure_dirs

DATASET_ID: Final[str] = "vfth-yucv"
DOMAIN: Final[str] = "www.datos.gov.co"
BATCH_SIZE: Final[int] = 5_000
DEFAULT_TIMEOUT: Final[int] = 300

# Estaciones piloto (codigo → (nombre, cuenca))
ESTACIONES_PILOTO: Final[dict[str, tuple[str, str]]] = {
    "0035077180": ("Culima - Río Bata", "Orinoquía"),
    "0026157190": ("Río Claro",          "Cauca"),
    "0021167080": ("La Mora",            "Alto Magdalena"),
}


def download(
    estaciones: dict[str, tuple[str, str]] | None = None,
    year_start: int = 2015,
    year_end: int = 2024,
    out_path: Path | None = None,
    force: bool = False,
    verbose: bool = True,
) -> Path:
    """Descarga nivel hidrométrico por bloques anuales y lo agrega a diario.

    Args:
        estaciones: dict ``{codigo: (nombre, cuenca)}``. Por defecto ``ESTACIONES_PILOTO``
        year_start, year_end: rango inclusivo
        out_path: CSV de salida. ``None`` usa ``paths.SIRH_CSV``
        force: re-descargar aunque ya exista
        verbose: imprimir progreso

    Returns:
        Path al CSV generado.
    """
    ensure_dirs()
    if out_path is None:
        out_path = _paths.SIRH_CSV

    if out_path.exists() and not force:
        if verbose:
            print(f"[sirh] cache hit: {out_path}")
        return out_path

    # Import perezoso: sodapy solo si realmente se descarga
    from sodapy import Socrata

    client = Socrata(DOMAIN, None, timeout=DEFAULT_TIMEOUT)
    estaciones = estaciones or ESTACIONES_PILOTO
    todos: list[pd.DataFrame] = []

    for codigo, (nombre, _cuenca) in estaciones.items():
        if verbose:
            print(f"[sirh] {codigo} — {nombre}")
        for anio in range(year_start, year_end + 1):
            df_anio = _descargar_anio(client, codigo, anio, verbose)
            if df_anio is not None:
                todos.append(df_anio)

    if not todos:
        raise RuntimeError("No se descargó ningún registro. Revisa tu conexión.")

    df = _procesar_a_diario(pd.concat(todos, ignore_index=True))
    df.to_csv(out_path, index=False)

    if verbose:
        print(f"[sirh] guardado {len(df):,} filas en {out_path}")
    return out_path


def load(
    estaciones: list[str] | None = None,
    auto_download: bool = False,
) -> pd.DataFrame:
    """Carga el CSV diario de niveles. Si no existe y ``auto_download=True``, descarga.

    Args:
        estaciones: lista de códigos a filtrar. ``None`` = todas
        auto_download: ``True`` dispara `download()` si falta el CSV

    Returns:
        DataFrame con columnas: ``codigoestacion``, ``fecha``, ``nivel_m``.
    """
    if not _paths.SIRH_CSV.exists():
        if auto_download:
            download()
        else:
            raise FileNotFoundError(
                f"{_paths.SIRH_CSV} no existe. Corre `sirh.download()` primero "
                "(tarda ~20 min, 3 estaciones × 10 años)."
            )

    df = pd.read_csv(_paths.SIRH_CSV, parse_dates=["fecha"])
    if estaciones is not None:
        df = df[df["codigoestacion"].isin(estaciones)]
    return df.reset_index(drop=True)


# ==========================================================
# Internos
# ==========================================================
def _descargar_anio(
    client,
    codigo: str,
    anio: int,
    verbose: bool,
    max_reintentos: int = 2,
) -> pd.DataFrame | None:
    """Descarga un año completo para una estación, con paginación y reintentos."""
    offset = 0
    intentos = 0
    chunks: list[pd.DataFrame] = []

    while True:
        where = (
            f"codigoestacion = '{codigo}' AND "
            f"fechaobservacion between '{anio}-01-01T00:00:00.000' "
            f"AND '{anio}-12-31T23:59:59.000'"
        )
        try:
            resp = client.get(
                DATASET_ID,
                where=where,
                limit=BATCH_SIZE,
                offset=offset,
                order="fechaobservacion ASC",
            )
        except Exception as e:
            intentos += 1
            if intentos >= max_reintentos:
                if verbose:
                    print(f"  {anio}: fallo tras {max_reintentos} intentos — skip ({e})")
                return None
            time.sleep(10)
            continue

        if not resp:
            break

        df_chunk = pd.DataFrame.from_records(resp)
        df_chunk["_cod"] = codigo
        chunks.append(df_chunk)

        if len(resp) < BATCH_SIZE:
            break
        offset += BATCH_SIZE
        time.sleep(0.3)

    if not chunks:
        if verbose:
            print(f"  {anio}: sin datos")
        return None

    return pd.concat(chunks, ignore_index=True)


def _procesar_a_diario(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia, tipifica y agrega a resolución diaria (max por día)."""
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fechaobservacion"])
    df["nivel_m"] = pd.to_numeric(df["valorobservado"], errors="coerce")
    df = df.dropna(subset=["nivel_m"])

    df_diario = (
        df.set_index("fecha")
          .groupby("codigoestacion")["nivel_m"]
          .resample("D").max()
          .reset_index()
    )
    return df_diario
