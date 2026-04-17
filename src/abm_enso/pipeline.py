"""Pipeline orquestador del ABM-ENSO-Colombia.

Fases:
    descargar_todas()    — Fase 2: descarga las 5 fuentes de datos
    calibrar_modelo()    — Fase 3: calibra β₁, θ, κ vs datos reales
    simular_escenario()  — Fase 4: corre el ABM en Mesa
"""

from __future__ import annotations

import time
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
    """Descarga las fuentes indicadas y retorna el resumen."""
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
        except Exception as e:
            dt = time.perf_counter() - t0
            results[fuente] = (False, f"{type(e).__name__}: {e}")
            if not skip_on_error:
                raise

    # Resumen
    print(f"\n{'='*60}\nRESUMEN\n{'='*60}")
    for fuente, (ok, info) in results.items():
        marca = "✓" if ok else "✗"
        print(f"  {marca}  {fuente:10s} {info}")

    return results


# ==========================================================
# Fase 3 — Calibración
# ==========================================================
def calibrar_modelo(verbose: bool = True):
    """Calibra β₁, θ, κ contra datos reales y guarda los parámetros."""
    import json

    import pandas as pd

    from abm_enso.analysis import (
        calibracion_beta,
        calibracion_theta_kappa,
        filtros,
        lorenz,
        metricas,
    )
    from abm_enso.data import era5 as era5_mod, oni as oni_mod, simma as simma_mod
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
    df_era5 = era5_mod.load()
    df_simma = simma_mod.load(tipo=["Deslizamiento", "Flujo"])

    # 2. Filtrar ENSO
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

    # 4. Calibrar β₁ con OLS en banda ENSO + lag 1 mes
    if verbose:
        print("[4/5] Calibrando β₁ con OLS (ONI lag-1 vs ERA5 precip, banda ENSO)...")
    precip_enso = filtros.filtrar_fuente(df_era5["precip_mm_mes"], quitar_clima=True)
    oni_lag = oni_enso.shift(1)
    idx_comun_beta = precip_enso.index.intersection(oni_lag.dropna().index)
    beta_result = calibracion_beta.ols_beta1(
        oni_lag.loc[idx_comun_beta],
        precip_enso.loc[idx_comun_beta],
    )
    if verbose:
        print(f"       β₁ = {beta_result['beta_1']:.2f} mm/mes por °C ONI")
        print(f"       r² = {beta_result['r_cuadrado']:.3f}")

    # 5. Grid search θ, κ contra SIMMA
    if verbose:
        print("[5/5] Grid search θ, κ contra eventos SIMMA...")
    simma_mensual = (
        df_simma.dropna(subset=["fecha_evento"])
        .set_index("fecha_evento")
        .resample("MS")
        .size()
    )
    idx_comun = df_era5.index.intersection(simma_mensual.index)
    if len(idx_comun) < 50:
        if verbose:
            print(f"       ⚠  Solo {len(idx_comun)} meses en común — ampliando con ceros")
        simma_mensual = simma_mensual.reindex(df_era5.index, fill_value=0)
        idx_comun = df_era5.index

    precip_alineado = df_era5["precip_mm_mes"].loc[idx_comun].values
    eventos_obs = (simma_mensual.loc[idx_comun] > 5).values

    resultado = calibracion_theta_kappa.grid_search_f1(
        precip=precip_alineado,
        eventos_obs=eventos_obs,
    )
    if verbose:
        print(f"       θ* = {resultado.theta_opt:.3f}")
        print(f"       κ* = {resultado.kappa_opt:.3f}")
        print(f"       F1 = {resultado.f1_opt:.3f}")

    # Guardar
    out_parquet = _paths.DATA_PROCESSED / "cuencas_parametros.parquet"
    out_json = _paths.DATA_PROCESSED / "calibracion_resumen.json"

    df_params = pd.DataFrame([{
        "tipo_suelo":        "default",
        "beta_1":            beta_result["beta_1"],
        "alpha":             beta_result["alpha"],
        "theta":             resultado.theta_opt,
        "kappa":             resultado.kappa_opt,
        "r_beta":            beta_result["r"],
        "f1_theta_kappa":    resultado.f1_opt,
    }])
    df_params.to_parquet(out_parquet, index=False)

    with open(out_json, "w") as f:
        json.dump({
            "beta_1":   beta_result["beta_1"],
            "theta":    resultado.theta_opt,
            "kappa":    resultado.kappa_opt,
            "f1":       resultado.f1_opt,
            "r_lorenz": r_lorenz,
            "r_beta":   beta_result["r"],
        }, f, indent=2)

    if verbose:
        print(f"\n✓ Parámetros guardados en {out_parquet}")
        print(f"✓ Resumen guardado en {out_json}")

    return df_params


# ==========================================================
# Fase 4 — Simulación
# ==========================================================
def simular_escenario(
    scenario: str = "historico",
    n_meses: int = 36,
    replicas: int = 1,
    ruido: float = 0.0,
    seed: int = 42,
    validar: bool = False,
    verbose: bool = True,
    theta_override: float | None = None,
    kappa_override: float | None = None,
):
    """Corre el ABM bajo un escenario ENSO específico.

    Args:
        scenario: 'nina-2010', 'nino-2015', 'neutro', 'historico', 'lorenz'
        n_meses: duración (ignorado para 'historico')
        replicas: réplicas Monte Carlo (útil con ruido>0)
        ruido: std del ruido ε en precipitación (fracción de climatología)
        seed: semilla base
        validar: si True y scenario='historico', valida vs SIMMA
        theta_override, kappa_override: override del Parquet (para experimentar)
    """
    import json

    import pandas as pd

    from abm_enso.data import cuencas as cuencas_mod
    from abm_enso.model import ModeloCuencas, escenarios, validacion
    from abm_enso.utils import paths as _paths

    if verbose:
        print("\n" + "=" * 60)
        print(f"SIMULACIÓN — escenario: {scenario}")
        print("=" * 60)

    # Cargar cuencas
    if verbose:
        print("\n[1/4] Cargando cuencas...")
    gdf = cuencas_mod.load()
    if verbose:
        print(f"       {len(gdf)} cuencas cargadas")
        if "area_hidrografica" in gdf.columns:
            dist = gdf["area_hidrografica"].value_counts()
            for area, n in dist.items():
                print(f"         {area:20s} {n:3d}")

    # Generar ONI
    if verbose:
        print(f"[2/4] Generando escenario ONI: {scenario}")
    gen = escenarios.get(scenario)
    if scenario == "historico":
        oni_serie = gen(inicio="2010-01-01", fin="2012-12-31")
    elif scenario == "lorenz":
        oni_serie = gen(n_meses=n_meses, seed=seed)
    else:
        oni_serie = gen(n_meses=n_meses)
    if verbose:
        print(f"       {len(oni_serie)} meses generados (ONI rango [{oni_serie.min():.2f}, {oni_serie.max():.2f}])")

    # Parámetros calibrados
    theta, kappa = 0.60, 0.22  # defaults más razonables
    params_path = _paths.DATA_PROCESSED / "cuencas_parametros.parquet"
    if params_path.exists():
        df_params = pd.read_parquet(params_path)
        if len(df_params) > 0:
            theta = float(df_params.iloc[0]["theta"])
            kappa = float(df_params.iloc[0]["kappa"])

    # Overrides
    if theta_override is not None:
        theta = theta_override
    if kappa_override is not None:
        kappa = kappa_override

    if verbose:
        print(f"       θ={theta:.3f}, κ={kappa:.3f}")

    # Correr réplicas
    if verbose:
        print(f"[3/4] Corriendo {replicas} réplica(s) con ruido={ruido}...")
    resultados = []
    for i in range(replicas):
        m = ModeloCuencas(
            gdf_cuencas=gdf,
            oni_serie=oni_serie,
            theta=theta,
            kappa=kappa,
            ruido_precip=ruido,
            seed=seed + i,
        )
        m.run()
        df_run = m.resumen_temporal()
        df_run["replica"] = i
        resultados.append(df_run)
        if verbose:
            activ_total = df_run["n_activaciones"].sum()
            h_max = df_run["humedad_media"].max()
            print(f"       réplica {i+1}/{replicas}: {activ_total} activaciones, H_max={h_max:.0f}")

    # Guardar CSV
    df_full = pd.concat(resultados, ignore_index=True)
    out_csv = _paths.DATA_PROCESSED / f"simulacion_{scenario}.csv"
    df_full.to_csv(out_csv, index=False)
    if verbose:
        print(f"\n✓ Resultados guardados en {out_csv}")

    # Validación
    if validar and scenario == "historico":
        if verbose:
            print("\n[4/4] Validando contra SIMMA 2010-2012...")
        resultado = validacion.validar_contra_simma(m)
        if verbose:
            print(f"       r    = {resultado['r']}")
            print(f"       RMSE = {resultado['rmse']:.2f}")
            print(f"       F1   = {resultado['f1']:.3f}")
            print(f"       n meses = {resultado['n_meses']}")

        out_val = _paths.DATA_PROCESSED / f"validacion_{scenario}.json"
        with open(out_val, "w") as f:
            json.dump({
                "r":       resultado["r"],
                "rmse":    resultado["rmse"],
                "f1":      resultado["f1"],
                "n_meses": resultado["n_meses"],
            }, f, indent=2, default=str)

    return resultados
