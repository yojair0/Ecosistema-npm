# stratification/01_grid_base.py -- grid-based stratification on dataset B.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from common import (load_dataset_b, split_halves, build_cell_partition,
                     merge_small_strata, partition_metrics, validation_r2,
                     strata_table, write_metrics, write_strata,
                     write_results_md, df_to_markdown, band_labels,
                     SEED, MIN_STRATUM_REPORT)

# ── Constants ────────────────────────────────────────────────────────
TECHNIQUE = "01_grid_base"
GRANULARITIES = {
    "coarse": {"fi_edges": [1, 10], "fo_edges": [1, 10]},
    "medium": {"fi_edges": [1, 10, 100], "fo_edges": [1, 3, 10]},
    "fine":   {"fi_edges": [1, 10, 100, 1000], "fo_edges": [1, 3, 10, 50]},
}
CENSUS_OPTIONS = [False, True]
CENSUS_THRESHOLD = 1000
MIN_N = 500

def main():
    print("Loading dataset B ...")
    df = load_dataset_b()
    n = len(df)
    mask_fit, mask_test = split_halves(n, SEED)
    n_fit = int(mask_fit.sum())
    # Scale MIN_N to the fit half so effective minimum is ~500 on full B.
    min_n_fit = round(MIN_N * n_fit / n)
    print(f"  n={n:,}  fit={n_fit:,}  min_n_fit={min_n_fit}")
    metric_rows = []
    strata_tables = []
    configs = {}
    for gran_name, edges in GRANULARITIES.items():
        fi_e = edges["fi_edges"]
        fo_e = edges["fo_edges"]
        for census in CENSUS_OPTIONS:
            tag = "census" if census else "nocensus"
            config = f"{gran_name}_{tag}"
            strata, info = build_cell_partition(
                df, fi_e, fo_e, census, CENSUS_THRESHOLD)
            strata, info = merge_small_strata(
                strata, info, min_n_fit, mask=mask_fit)
            met = partition_metrics(df, strata)
            val = validation_r2(df, strata, mask_fit, mask_test)
            params = (f"{gran_name}, fi={band_labels(fi_e)}, "
                      f"fo={band_labels(fo_e)}, "
                      f"censo={'sí' if census else 'no'}, min_n={MIN_N}")
            row = {"config": config, "params": params}
            row.update(met)
            row.update(val)
            metric_rows.append(row)
            st = strata_table(df, strata, info, TECHNIQUE, config)
            strata_tables.append(st)
            configs[config] = {"info": info, "strata_df": st}
            print(f"  {config:25s}  K={met['K']:3d}  min_n={met['min_n']:7,}"
                  f"  r2_fi={met['r2_log_fi']:.4f}"
                  f"  r2_fo={met['r2_log_fo']:.4f}")
    # ── Write CSV outputs ────────────────────────────────────────────
    write_metrics(TECHNIQUE, metric_rows)
    write_strata(TECHNIQUE, pd.concat(strata_tables, ignore_index=True))
    # ── Build markdown ───────────────────────────────────────────────
    lines = ["# Estratificación por cuadrícula base\n"]
    lines.append("## Parámetros\n")
    lines.append(f"- Semilla: {SEED}")
    lines.append(f"- Mínimo por estrato (sobre B completo): {MIN_N}")
    lines.append(f"- Mínimo escalado a mitad de ajuste: {min_n_fit}")
    lines.append(f"- Umbral de censo: Fan-In ≥ {CENSUS_THRESHOLD}")
    lines.append(f"- Población B: {n:,} paquetes\n")
    lines.append("### Granularidades\n")
    for gran_name, edges in GRANULARITIES.items():
        fi_lab = band_labels(edges["fi_edges"])
        fo_lab = band_labels(edges["fo_edges"])
        lines.append(f"- **{gran_name}**: Fan-In [{', '.join(fi_lab)}]"
                      f" — Fan-Out [{', '.join(fo_lab)}]")
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
    write_results_md(TECHNIQUE, "\n".join(lines))
    print("Done.")

if __name__ == "__main__":
    main()
