# stratification/04_clustering.py -- k-means clustering on dataset B.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
try:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.metrics import davies_bouldin_score
except ImportError:
    sys.exit("scikit-learn is required: pip install scikit-learn")
from common import (load_dataset_b, split_halves, partition_metrics,
                     validation_r2, strata_table, write_metrics, write_strata,
                     write_results_md, df_to_markdown, SEED, VARS,
                     ZERO_CELL_NAMES)

# ── Constants ────────────────────────────────────────────────────────
TECHNIQUE = "04_clustering"
N_CLUSTERS = [4, 8, 12]
FIT_SAMPLE_MAX = 300_000
SILHOUETTE_SAMPLE = 20_000
DB_SAMPLE = 100_000
PREDICT_CHUNK = 500_000
LOG_VARS = ["n_versions", "n_maintainers", "n_keywords",
            "n_peer", "n_opt", "fan_in_dev", "fan_out_dev"]
BIN_VARS = ["has_github", "deprecated", "scoped"]
RAW_VARS = ["age_years"]

# ── Transform matrix ────────────────────────────────────────────────
def build_matrix(df, mask):
    cols = []
    for v in VARS:
        a = df[v].values[mask].astype(np.float32)
        if v in LOG_VARS:
            a = np.log1p(a)
        cols.append(a)
    return np.column_stack(cols)
def standardise(X, mu, sd):
    return ((X - mu) / np.where(sd > 0, sd, 1.0)).astype(np.float32)

# ── Main ─────────────────────────────────────────────────────────────
def main():
    print("Loading dataset B ...")
    df = load_dataset_b()
    n = len(df)
    mask_fit, mask_test = split_halves(n, SEED)
    zc = df["zero_cell"].values
    not_iso = zc != 0
    n_not_iso = int(not_iso.sum())
    print(f"  n={n:,}  not_isolated={n_not_iso:,}")
    # Build raw transformed matrix for non-isolated packages
    X_raw = build_matrix(df, not_iso)
    metric_rows = []
    strata_tables_list = []
    configs = {}
    for k in N_CLUSTERS:
        config = f"k{k}"
        # Fit sample: non-isolated in fit half
        fit_idx = np.where(not_iso & mask_fit)[0]
        rng = np.random.default_rng(SEED)
        if len(fit_idx) > FIT_SAMPLE_MAX:
            sample_idx = rng.choice(len(fit_idx), FIT_SAMPLE_MAX, replace=False)
            fit_idx = fit_idx[sample_idx]
        # Map fit_idx (global) to positions in X_raw (non-isolated order)
        global_to_raw = np.full(n, -1, dtype=np.int64)
        global_to_raw[not_iso] = np.arange(n_not_iso)
        raw_fit = global_to_raw[fit_idx]
        X_fit = X_raw[raw_fit]
        mu = X_fit.mean(axis=0)
        sd = X_fit.std(axis=0)
        X_fit_s = standardise(X_fit, mu, sd)
        km = KMeans(n_clusters=k, n_init=3, random_state=SEED)
        km.fit(X_fit_s)
        # Predict in chunks
        X_std_all = standardise(X_raw, mu, sd)
        labels = np.empty(n_not_iso, dtype=np.int32)
        for start in range(0, n_not_iso, PREDICT_CHUNK):
            end = min(start + PREDICT_CHUNK, n_not_iso)
            labels[start:end] = km.predict(X_std_all[start:end])
        del X_std_all
        # Build global strata: 0 = Aislado, 1..k = clusters
        strata = np.full(n, 0, dtype=np.int32)
        strata[not_iso] = labels + 1
        # Silhouette on sample
        sil_idx = rng.choice(n_not_iso, min(SILHOUETTE_SAMPLE, n_not_iso),
                             replace=False)
        X_sil = standardise(X_raw[sil_idx], mu, sd)
        sil = float(silhouette_score(X_sil, labels[sil_idx]))
        # Davies-Bouldin on sample
        db_idx = rng.choice(n_not_iso, min(DB_SAMPLE, n_not_iso),
                            replace=False)
        X_db = standardise(X_raw[db_idx], mu, sd)
        db = float(davies_bouldin_score(X_db, labels[db_idx]))
        # Partition metrics
        met = partition_metrics(df, strata)
        val = validation_r2(df, strata, mask_fit, mask_test)
        params = (f"k={k}, n_init=3, fit_max={FIT_SAMPLE_MAX}")
        row = {"config": config, "params": params}
        row.update(met)
        row.update(val)
        row["silhouette"] = sil
        row["davies_bouldin"] = db
        metric_rows.append(row)
        # Info for strata_table
        info_rows = [{"stratum": 0, "description": ZERO_CELL_NAMES[0]}]
        for c in range(k):
            info_rows.append({"stratum": c + 1,
                              "description": f"Cluster {c}"})
        info_df = pd.DataFrame(info_rows)
        st = strata_table(df, strata, info_df, TECHNIQUE, config)
        strata_tables_list.append(st)
        # Cluster profile
        prof_rows = []
        for c in range(k):
            cmask = labels == c
            sub = df.loc[not_iso][cmask]
            cnt = len(sub)
            pr = {"cluster": c, "n": cnt,
                  "share": cnt / n_not_iso}
            for v in ["n_versions", "n_maintainers", "n_keywords",
                       "age_years"]:
                pr[f"med_{v}"] = float(np.median(sub[v].values))
            pr["pct_github"] = sub["has_github"].mean() * 100
            pr["pct_scoped"] = sub["scoped"].mean() * 100
            pr["pct_deprecated"] = sub["deprecated"].mean() * 100
            pr["pct_fi_dev_gt0"] = (sub["fan_in_dev"].values > 0).mean() * 100
            pr["pct_fo_dev_gt0"] = (sub["fan_out_dev"].values > 0).mean() * 100
            sub_zc = sub["zero_cell"].values
            for code in [1, 2, 3]:
                pr[f"pct_{ZERO_CELL_NAMES[code]}"] = (
                    (sub_zc == code).mean() * 100)
            prof_rows.append(pr)
        prof_df = pd.DataFrame(prof_rows)
        configs[config] = {"strata_df": st, "profile": prof_df}
        print(f"  {config:6s}  K={met['K']:3d}  sil={sil:.4f}"
              f"  db={db:.4f}"
              f"  r2_fi={met['r2_log_fi']:.4f}"
              f"  r2_fo={met['r2_log_fo']:.4f}")
    del X_raw
    # ── Write outputs ────────────────────────────────────────────────
    write_metrics(TECHNIQUE, metric_rows)
    write_strata(TECHNIQUE, pd.concat(strata_tables_list, ignore_index=True))
    # ── Markdown ─────────────────────────────────────────────────────
    lines = ["# Estratificación por clustering (k-means)\n"]
    lines.append("## Parámetros\n")
    lines.append(f"- Semilla: {SEED}")
    lines.append(f"- Clusters probados: {N_CLUSTERS}")
    lines.append(f"- n_init: 3")
    lines.append(f"- Máximo de filas para ajuste: {FIT_SAMPLE_MAX:,}")
    lines.append(f"- Muestra para silueta: {SILHOUETTE_SAMPLE:,}")
    lines.append(f"- Muestra para Davies-Bouldin: {DB_SAMPLE:,}")
    lines.append(f"- Variables: {', '.join(VARS)}")
    lines.append(f"- Transformación: log1p para conteos "
                 f"({', '.join(LOG_VARS)}), "
                 f"binarias como 0/1, age_years sin transformar")
    lines.append("- Estandarización con media y desviación de la muestra "
                 "de ajuste\n")
    lines.append("## Métricas\n")
    met_df = pd.DataFrame(metric_rows)
    show_cols = ["config", "K", "min_n", "n_under_min",
                 "silhouette", "davies_bouldin",
                 "r2_log_fi", "r2_log_fo", "r2_log_n_versions", "r2_age",
                 "eff_prop_log_fi", "eff_neyman_log_fi",
                 "eff_prop_log_fo", "eff_neyman_log_fo",
                 "r2_log_fi_train", "r2_log_fi_test",
                 "r2_log_fo_train", "r2_log_fo_test"]
    lines.append(df_to_markdown(met_df[show_cols]))
    lines.append("")
    lines.append("## Tabla de estratos y perfil por configuración\n")
    show_st = ["stratum", "description", "n", "share",
               "mean_log_fi", "mean_log_fo",
               "median_n_versions", "median_age"]
    for config, data in configs.items():
        lines.append(f"### {config}\n")
        lines.append("**Estratos**\n")
        lines.append(df_to_markdown(data["strata_df"][show_st]))
        lines.append("")
        lines.append("**Perfil por cluster**\n")
        lines.append(df_to_markdown(data["profile"]))
        lines.append("")
    write_results_md(TECHNIQUE, "\n".join(lines))
    print("Done.")

if __name__ == "__main__":
    main()
