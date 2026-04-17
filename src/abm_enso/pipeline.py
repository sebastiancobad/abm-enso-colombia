"""Orquestador de descarga — importable por el CLI y el script.

Concentra la lógica que antes vivía solo en ``scripts/download_all.py``
para poder llamarla tanto desde CLI (``abm-enso download``) como desde
un ``python scripts/download_all.py`` directo.
"""

from __future__ import annotations

import time
import traceback
from typing import Iterable

from abm_enso.data import cuencas, era5, oni, simma, sirh
from abm_enso.utils.paths import ensure_dirs

FUENTES_DISPONIBLES = ("oni", "era5", "sirh", "simma", "cuencas")


def descargar_todas(
    solo: Iterable[str] = FUENTES_DISPONIBLES,
    force: bool = False,
    era5_mode: str = "daily",
    era5_chunk_years: int = 5,
    skip_on_error: bool = False,
) -> dict[str, tuple[bool, str]]:
    """Descarga las fuentes indicadas y retorna el resumen.

    Args:
        solo: fuentes a descargar (subset de FUENTES_DISPONIBLES)
        force: re-descargar aunque exista cache
        era5_mode: ``"daily"`` o ``"monthly"``
        era5_chunk_years: años por request ERA5 (default 5; baja a 2-3
            si Copernicus sigue rechazando por cost limits)
        skip_on_error: continuar con las siguientes si una falla

    Returns:
        dict ``{fuente: (ok: bool, info: str)}``
    """
    ensure_dirs()
    results: dict[str, tuple[bool, str]] = {}

    for fuente in solo:
        if fuente not in FUENTES_DISPONIBLES:
            results[fuente] = (False, "desconocida")
            continue

        print(f"\n{'='*60}\n→ {fuente.upper()}\n{'='*60}")
        t0 = time.perf_counter()
        try:
            if fuente == "oni":
                oni.download(force=force)
            elif fuente == "era5":
                era5.download(mode=era5_mode, force=force, chunk_years=era5_chunk_years)
            elif fuente == "sirh":
                sirh.download(force=force)
            elif fuente == "simma":
                simma.download(force=force)
            elif fuente == "cuencas":
                cuencas.download(force=force)
            dt = time.perf_counter() - t0
            results[fuente] = (True, f"{dt:.1f}s")
            print(f"[ok] {fuente} completo en {dt:.1f}s")
        except Exception as e:
            dt = time.perf_counter() - t0
            results[fuente] = (False, f"{e.__class__.__name__}: {e}")
            print(f"[FAIL] {fuente} en {dt:.1f}s — {e}")
            traceback.print_exc()
            if not skip_on_error:
                break

    _imprimir_resumen(results)
    return results


def _imprimir_resumen(results: dict[str, tuple[bool, str]]) -> None:
    print(f"\n{'='*60}\nRESUMEN\n{'='*60}")
    for fuente, (ok, info) in results.items():
        status = "✓" if ok else "✗"
        print(f"  {status}  {fuente:10s} {info}")


# ==========================================================
# Fase 3 — Calibración
# ==========================================================
def calibrar_modelo(verbose: bool = True):
    """Pipeline completo de calibración: Butterworth + Lorenz + β₁ + (θ, κ).

    Lee los datos procesados, calibra todos los parámetros contra SIMMA,
    guarda el resultado en ``data/processed/cuencas_parametros.parquet``.

    Returns:
        DataFrame con los parámetros calibrados por grupo.
    """
    import json

    import pandas as pd

    from abm_enso.analysis import (
        calibracion_beta,
        calibracion_theta_kappa,
        filtros,
        lorenz,
        metricas,
    )
    from abm_enso.data import era5, oni as oni_mod, simma as simma_mod
    from abm_enso.utils import paths as _paths

    _paths.ensure_dirs()

    if verbose:
        print("\n" + "=" * 60)
        print("CALIBRACIÓN DEL MODELO 1")
        print("=" * 60)

    # 1. Cargar datos
    if verbose:
        print("\n[1/5] Cargando datos...")
    df_oni = oni_mod.load()["oni"].dropna()
    df_era5 = era5.load()
    df_simma = simma_mod.load(tipo=["Deslizamiento", "Flujo"])

    # 2. Filtrar ENSO de ONI
    if verbose:
        print("[2/5] Filtrando señal ENSO (Butterworth 2-7 años)...")
    oni_enso = filtros.butterworth_enso(df_oni)

    # 3. Calibrar Lorenz
    if verbose:
        print("[3/5] Calibrando Lorenz al ONI filtrado...")
    oni_lorenz = lorenz.generar_oni_sintetico(oni_enso, T=2000.0, seed=42)
    r_lorenz = metricas.pearson_r(oni_lorenz, oni_enso)
    if verbose:
        print(f"       r(Lorenz, ONI_filtrado) = {r_lorenz:.3f}")

    # 4. Calibrar β₁ (OLS nacional, único bucket por ahora — sin shapefile por cuenca)
    if verbose:
        print("[4/5] Calibrando β₁ con OLS (ONI lag-1 vs ERA5 precip, banda ENSO)...")
    # Filtrar ambas en banda ENSO
    precip_enso = filtros.filtrar_fuente(df_era5["precip_mm_mes"], quitar_clima=True)
    # Lag de 1 mes: la respuesta de lluvia colombiana al ONI es ~1 mes tardía
    oni_lag = oni_enso.shift(1)
    # Alinear
    idx_comun = precip_enso.index.intersection(oni_lag.dropna().index)
    beta_result = calibracion_beta.ols_beta1(
        oni_lag.loc[idx_comun],
        precip_enso.loc[idx_comun],
    )
    if verbose:
        print(f"       β₁ = {beta_result['beta_1']:.2f} mm/mes por °C ONI")
        print(f"       r² = {beta_result['r_cuadrado']:.3f}")

    # 5. Calibrar θ y κ contra SIMMA
    if verbose:
        print("[5/5] Grid search θ, κ contra eventos SIMMA...")
    # Agregar SIMMA a mensual
    simma_mensual = (
        df_simma.dropna(subset=["fecha_evento"])
        .set_index("fecha_evento")
        .resample("MS").size()
    )
    # Alinear con ERA5 (rango 1981-2024)
    idx_comun = df_era5.index.intersection(simma_mensual.index)
    if len(idx_comun) < 50:
        if verbose:
            print(f"       ⚠  Solo {len(idx_comun)} meses en común — ampliando con ceros")
        simma_mensual = simma_mensual.reindex(df_era5.index, fill_value=0)
        idx_comun = df_era5.index

    precip_alineado = df_era5["precip_mm_mes"].loc[idx_comun].values
    # Umbral: evento = mes con más de 5 eventos SIMMA
    eventos_obs = (simma_mensual.loc[idx_comun] > 5).values

    resultado = calibracion_theta_kappa.grid_search_f1(
        precip=precip_alineado,
        eventos_obs=eventos_obs,
    )
    if verbose:
        print(f"       θ* = {resultado.theta_opt:.3f}")
        print(f"       κ* = {resultado.kappa_opt:.3f}")
        print(f"       F1 = {resultado.f1_opt:.3f}")

    # Guardar resultado
    out_parquet = _paths.DATA_PROCESSED / "cuencas_parametros.parquet"
    out_json = _paths.DATA_PROCESSED / "calibracion_resumen.json"

    df_params = pd.DataFrame([{
        "tipo_suelo":  "default",
        "beta_1":      beta_result["beta_1"],
        "alpha":       beta_result["alpha"],
        "theta":       resultado.theta_opt,
        "kappa":       resultado.kappa_opt,
        "r_beta":      beta_result["r"],
        "f1_theta_kappa": resultado.f1_opt,
    }])
    df_params.to_parquet(out_parquet, index=False)

    resumen = {
        "beta_1":     beta_result["beta_1"],
        "theta":      resultado.theta_opt,
        "kappa":      resultado.kappa_opt,
        "f1":         resultado.f1_opt,
        "r_lorenz":   r_lorenz,
        "r_beta":     beta_result["r"],
    }
    with open(out_json, "w") as f:
        json.dump(resumen, f, indent=2)

    if verbose:
        print(f"\n✓ Parámetros guardados en {out_parquet}")
        print(f"✓ Resumen guardado en {out_json}")

    return df_params
