# stratification/02_optimal_cuts.py -- Dalenius-Hodges optimal cuts on dataset B.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from common import (load_dataset_b, split_halves, build_cell_partition,
                     merge_small_strata, partition_metrics, validation_r2,
                     strata_table, write_metrics, write_strata,
                     write_results_md, df_to_markdown, band_labels, SEED)

# ── Constants ────────────────────────────────────────────────────────
TECHNIQUE = "02_optimal_cuts"
N_BANDS = [2, 3, 4]
CENSUS_OPTIONS = [False, True]
CENSUS_THRESHOLD = 1000
MIN_N = 500

# ── Dalenius-Hodges cut computation ──────────────────────────────────
def dalenius_hodges_edges(values, n_bands):
    # Fine classes: each integer 1..min(max_val, 1000).
    # Above 1000: doubling intervals (1001, 2000, 4000, 8000, ...).
    if len(values) == 0:
        return [1]
    max_val = int(values.max())
    class_lo = list(range(1, min(max_val + 1, 1001)))
    if max_val >= 1001:
        class_lo.append(1001)
        e = 2000
        while e <= max_val:
            class_lo.append(e)
            e *= 2
    class_lo_arr = np.array(class_lo, dtype=np.int64)
    indices = np.searchsorted(class_lo_arr, values, side="right") - 1
    freq = np.bincount(indices, minlength=len(class_lo)).astype(np.float64)
    cum_sqrt = np.cumsum(np.sqrt(freq))
    total = cum_sqrt[-1]
    if total == 0.0:
        return [1]
    edges = [1]
    for k in range(1, n_bands):
        target = total * k / n_bands
        idx = int(np.argmin(np.abs(cum_sqrt - target)))
        if idx + 1 < len(class_lo):
            edge = class_lo[idx + 1]
            if edge not in edges:
                edges.append(edge)
    return sorted(edges)

# ── Main ─────────────────────────────────────────────────────────────
def main():
    print("Loading dataset B ...")
    df = load_dataset_b()
    n = len(df)
    mask_fit, mask_test = split_halves(n, SEED)
    n_fit = int(mask_fit.sum())
    min_n_fit = round(MIN_N * n_fit / n)
    print(f"  n={n:,}  fit={n_fit:,}  min_n_fit={min_n_fit}")
    # Positive values from fit half (computed once)
    fi_pos = df.loc[mask_fit & (df["fi"] > 0), "fi"].values
    fo_pos = df.loc[mask_fit & (df["fo"] > 0), "fo"].values
    metric_rows = []
    strata_tables = []
    configs = {}
    cuts_info = []
    for n_b in N_BANDS:
        for census in CENSUS_OPTIONS:
            tag = "census" if census else "nocensus"
            config = f"bands{n_b}_{tag}"
            fi_src = fi_pos[fi_pos < CENSUS_THRESHOLD] if census else fi_pos
            fi_edges = dalenius_hodges_edges(fi_src, n_b)
            fo_edges = dalenius_hodges_edges(fo_pos, n_b)
            reduced = len(fi_edges) < n_b or len(fo_edges) < n_b
            cuts_info.append({
                "config": config, "n_bands": n_b,
                "fi_edges": fi_edges, "fo_edges": fo_edges,
                "fi_labels": band_labels(fi_edges),
                "fo_labels": band_labels(fo_edges),
                "reduced": reduced,
            })
            strata_arr, info = build_cell_partition(
                df, fi_edges, fo_edges, census, CENSUS_THRESHOLD)
            strata_arr, info = merge_small_strata(
                strata_arr, info, min_n_fit, mask=mask_fit)
            met = partition_metrics(df, strata_arr)
            val = validation_r2(df, strata_arr, mask_fit, mask_test)
            params = (f"bands={n_b}, fi_edges={fi_edges}, "
                      f"fo_edges={fo_edges}, "
                      f"censo={'sí' if census else 'no'}, min_n={MIN_N}")
            row = {"config": config, "params": params}
            row.update(met)
            row.update(val)
            metric_rows.append(row)
            st = strata_table(df, strata_arr, info, TECHNIQUE, config)
            strata_tables.append(st)
            configs[config] = {"info": info, "strata_df": st}
            print(f"  {config:20s}  fi={fi_edges}  fo={fo_edges}"
                  f"  K={met['K']:3d}  min_n={met['min_n']:7,}"
                  f"  r2_fi={met['r2_log_fi']:.4f}"
                  f"  r2_fo={met['r2_log_fo']:.4f}")
    # ── Write CSV outputs ────────────────────────────────────────────
    write_metrics(TECHNIQUE, metric_rows)
    write_strata(TECHNIQUE, pd.concat(strata_tables, ignore_index=True))
    # ── Build markdown ───────────────────────────────────────────────
    lines = ["# Estratificación por cortes óptimos (Dalenius-Hodges)\n"]
    lines.append("## Parámetros\n")
    lines.append(f"- Semilla: {SEED}")
    lines.append(f"- Mínimo por estrato (sobre B completo): {MIN_N}")
    lines.append(f"- Mínimo escalado a mitad de ajuste: {min_n_fit}")
    lines.append(f"- Umbral de censo: Fan-In ≥ {CENSUS_THRESHOLD}")
    lines.append(f"- Población B: {n:,} paquetes")
    lines.append(f"- Bandas probadas: {N_BANDS}")
    lines.append("- Clases finas: cada entero de 1 a 1.000; "
                 "sobre 1.000, intervalos que duplican el ancho "
                 "(2.000, 4.000, 8.000, ...)\n")
    lines.append("## Cortes calculados por configuración\n")
    cut_rows = []
    for ci in cuts_info:
        cut_rows.append({
            "config": ci["config"],
            "n_bands": ci["n_bands"],
            "fi_edges": str(ci["fi_edges"]),
            "fi_bands": ", ".join(ci["fi_labels"]),
            "fo_edges": str(ci["fo_edges"]),
            "fo_bands": ", ".join(ci["fo_labels"]),
            "reducida": "sí" if ci["reduced"] else "no",
        })
    lines.append(df_to_markdown(pd.DataFrame(cut_rows)))
    lines.append("")
    lines.append("## Métricas de las 6 configuraciones\n")
    met_df = pd.DataFrame(metric_rows)
    show_cols = ["config", "K", "min_n", "n_under_min",
                 "r2_log_fi", "r2_log_fo", "r2_log_n_versions", "r2_age",
                 "eff_prop_log_fi", "eff_neyman_log_fi",
                 "eff_prop_log_fo", "eff_neyman_log_fo",
                 "r2_log_fi_train", "r2_log_fi_test",
                 "r2_log_fo_train", "r2_log_fo_test"]
    lines.append(df_to_markdown(met_df[show_cols]))
    lines.append("")
    lines.append("## Tabla de estratos por configuración\n")
    show_st = ["stratum", "description", "n", "share",
               "mean_log_fi", "mean_log_fo",
               "median_n_versions", "median_age"]
    for config, data in configs.items():
        lines.append(f"### {config}\n")
        lines.append(df_to_markdown(data["strata_df"][show_st]))
        lines.append("")
    lines.append("**Nota:** con censo, la última banda de Fan-In llega "
                 "hasta 999 aunque su etiqueta diga \"o más\".\n")
    write_results_md(TECHNIQUE, "\n".join(lines))
    print("Done.")

if __name__ == "__main__":
    main()
