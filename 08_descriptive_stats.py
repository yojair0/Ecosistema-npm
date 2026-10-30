"""
08_descriptive_stats.py -- Descriptive statistics and Spearman correlations
of the study population, in three situations:

  con familias                  population A, raw fan-in
  con familias, Fan-In externo  population A, fan-in counted only from
                                other scopes (fan_in_external)
  sin familias                  population B, raw fan-in

Corrections in this version:
  1. Adds the third situation, fan-in from other scopes.
  2. Adds package volume (file_count, unpacked). It is missing for some
     packages, so every correlation uses the pairs where both values exist,
     and the statistics report the share missing.
  3. A correlation that cannot be computed (a constant variable) is shown
     as missing, not as 0.
  4. The age is computed the same way whatever type the dates are stored as.
"""
import gc
from datetime import date
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import pandas as pd
from scipy.stats import rankdata

# ── Constants ─────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "07_inclusion_packages"
OUT_DIR = ROOT / "data" / "08_descriptive_stats"
FIG_DIR = OUT_DIR / "figures"
SNAPSHOT_DATE = date(2026, 9, 18)
EXTERNAL = "con familias, Fan-In externo"
DATASETS = [
    ("con familias", "population_with_families.parquet"),
    (EXTERNAL, "population_with_families.parquet"),
    ("sin familias", "population_without_families.parquet"),
]
SHORT = {"con familias": "Con familias", EXTERNAL: "Fan-In externo",
         "sin familias": "Sin familias"}
SLUG = {"con familias": "con_familias", EXTERNAL: "fan_in_externo",
        "sin familias": "sin_familias"}
COLS = [
    "fan_in", "fan_in_internal", "fan_in_external",
    "fan_out", "fan_in_dev", "fan_out_dev",
    "n_versions", "n_maintainers", "n_keywords",
    "n_peer", "n_opt", "file_count", "unpacked",
    "created_date", "has_github", "deprecated", "scope",
]
NUMERIC_VARS = [
    "fan_in", "fan_in_internal", "fan_in_external",
    "fan_out", "fan_in_dev", "fan_out_dev",
    "n_versions", "n_maintainers", "n_keywords",
    "n_peer", "n_opt", "file_count", "unpacked",
]
SPEARMAN_VARS = [
    "n_versions", "n_maintainers", "n_keywords",
    "n_peer", "n_opt", "age_years",
    "has_github", "deprecated", "scoped",
    "fan_in_dev", "fan_out_dev", "file_count", "unpacked",
]
TRAMO_EDGES = [(0, 0), (1, 9), (10, 99), (100, 999), (1000, None)]
TRAMO_LABELS = ["0", "1–9", "10–99", "100–999", "≥1000"]
HIST_BINS = np.arange(0, 6.5, 0.25)
REDUNDANCY_THRESHOLD = 0.7

# ── Helpers ───────────────────────────────────────────────────────────
def load_dataset(path):
    df = pd.read_parquet(path, columns=COLS)
    print(f"  memory: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
    # age_years from created_date; pd.to_datetime accepts dates stored as
    # Python objects, numpy datetimes or Arrow dates alike
    days = (pd.Timestamp(SNAPSHOT_DATE) - pd.to_datetime(df["created_date"])).dt.days
    df["age_years"] = days / 365.25
    # scoped
    df["scoped"] = (df["scope"].fillna("").astype(str) != "").astype(np.int8)
    # boolean cols → 0/1
    for col in ("has_github", "deprecated"):
        df[col] = df[col].fillna(0).astype(bool).astype(np.int8)
    df.drop(columns=["created_date", "scope"], inplace=True)
    return df
def zeros_grid(df):
    n = len(df)
    fi0 = df["fan_in"] == 0
    fo0 = df["fan_out"] == 0
    cells = [
        ("fan_in=0 & fan_out=0", int((fi0 & fo0).sum())),
        ("fan_in=0 & fan_out>0", int((fi0 & ~fo0).sum())),
        ("fan_in>0 & fan_out=0", int((~fi0 & fo0).sum())),
        ("fan_in>0 & fan_out>0", int((~fi0 & ~fo0).sum())),
    ]
    return [(lbl, cnt, cnt / n * 100) for lbl, cnt in cells]
def variable_stats(df):
    rows = []
    for v in NUMERIC_VARS:
        s = df[v]
        valid = s.dropna()
        rows.append({
            "variable": v,
            "pct_missing": s.isna().mean() * 100,
            "pct_zero": (valid == 0).mean() * 100,
            "median": float(np.median(valid)),
            "p90": float(np.percentile(valid, 90)),
            "p99": float(np.percentile(valid, 99)),
            "max": float(valid.max()),
        })
    s = df["age_years"]
    rows.append({
        "variable": "age_years",
        "pct_missing": s.isna().mean() * 100,
        "pct_zero": np.nan,
        "median": float(np.median(s)),
        "p90": float(np.percentile(s, 90)),
        "p99": float(np.percentile(s, 99)),
        "max": float(s.max()),
    })
    for v in ("has_github", "deprecated", "scoped"):
        rows.append({
            "variable": v,
            "pct_zero": np.nan,
            "median": np.nan,
            "p90": np.nan,
            "p99": np.nan,
            "max": np.nan,
            "pct_true": df[v].mean() * 100,
        })
    return pd.DataFrame(rows)
def tramo_table(df):
    fi = df["fan_in"].values
    rows = []
    n = len(df)
    for (lo, hi), label in zip(TRAMO_EDGES, TRAMO_LABELS):
        if hi is None:
            mask = fi >= lo
        else:
            mask = (fi >= lo) & (fi <= hi)
        sub = df[mask]
        cnt = int(mask.sum())
        rows.append({
            "tramo": label,
            "n": cnt,
            "pct": cnt / n * 100,
            "med_n_versions": float(np.median(sub["n_versions"])) if cnt else np.nan,
            "med_age_years": float(np.median(sub["age_years"])) if cnt else np.nan,
            "med_file_count": float(sub["file_count"].median()) if cnt else np.nan,
            "pct_github": sub["has_github"].mean() * 100 if cnt else np.nan,
            "pct_scoped": sub["scoped"].mean() * 100 if cnt else np.nan,
            "pct_deprecated": sub["deprecated"].mean() * 100 if cnt else np.nan,
            "sum_fi_internal": int(sub["fan_in_internal"].sum()),
            "sum_fi_external": int(sub["fan_in_external"].sum()),
            "pct_fi_internal_gt0": (sub["fan_in_internal"] > 0).mean() * 100 if cnt else np.nan,
        })
    return pd.DataFrame(rows)
def check_internal(df):
    return int((df["fan_in_internal"] > 0).sum())
# ── Spearman ──────────────────────────────────────────────────────────
def _pearson_on_ranks(rx, ry):
    # Pearson correlation on pre-computed ranks (= Spearman rho).
    mx = rx.mean()
    my = ry.mean()
    dx = rx - mx
    dy = ry - my
    num = (dx * dy).sum()
    den = np.sqrt((dx * dx).sum() * (dy * dy).sum())
    if den == 0:
        return np.nan  # a constant variable has no correlation
    return float(num / den)
def spearman_vs(df, target, variables, positive_only):
    if positive_only:
        mask = df[target].values > 0
        sub = df[mask]
    else:
        sub = df
    n = len(sub)
    if n < 3:
        return pd.Series(np.nan, index=variables)
    # Each pair uses the rows where both values exist (file_count and
    # unpacked are missing for some packages).
    t = sub[target].values.astype(float)
    rt = rankdata(t, method="average")
    result = {}
    for v in variables:
        x = sub[v].values.astype(float)
        m = ~np.isnan(x)
        if m.all():
            result[v] = _pearson_on_ranks(rt, rankdata(x, method="average"))
        elif m.sum() < 3:
            result[v] = np.nan
        else:
            result[v] = _pearson_on_ranks(rankdata(t[m], method="average"),
                                          rankdata(x[m], method="average"))
    return pd.Series(result)
def spearman_tables(df, label):
    print(f"  Spearman vs fan_in ({label})...")
    vars_in = list(SPEARMAN_VARS) + ["fan_out"]
    sp_in_all = spearman_vs(df, "fan_in", vars_in, False)
    print(f"    all done")
    sp_in_pos = spearman_vs(df, "fan_in", vars_in, True)
    print(f"    fan_in>0 done")
    sp_in = pd.DataFrame({"all": sp_in_all, "fan_in>0": sp_in_pos})
    print(f"  Spearman vs fan_out ({label})...")
    vars_out = list(SPEARMAN_VARS) + ["fan_in"]
    sp_out_all = spearman_vs(df, "fan_out", vars_out, False)
    print(f"    all done")
    sp_out_pos = spearman_vs(df, "fan_out", vars_out, True)
    print(f"    fan_out>0 done")
    sp_out = pd.DataFrame({"all": sp_out_all, "fan_out>0": sp_out_pos})
    return sp_in, sp_out
def corr_matrix(df):
    cols = ["fan_in", "fan_out"] + list(SPEARMAN_VARS)
    print(f"  full correlation matrix...")
    # Columns without missing values are ranked once; a pair that involves
    # a column with missing values uses the rows where both exist.
    ranks, partial = {}, set()
    for c in cols:
        x = df[c].values.astype(float)
        if np.isnan(x).any():
            partial.add(c)
        else:
            ranks[c] = rankdata(x, method="average")
    mat = np.empty((len(cols), len(cols)))
    for i, ci in enumerate(cols):
        for j, cj in enumerate(cols):
            if i == j:
                mat[i, j] = 1.0
            elif j > i:
                if ci in partial or cj in partial:
                    x = df[ci].values.astype(float)
                    y = df[cj].values.astype(float)
                    m = ~(np.isnan(x) | np.isnan(y))
                    rho = (_pearson_on_ranks(rankdata(x[m], method="average"),
                                             rankdata(y[m], method="average"))
                           if m.sum() >= 3 else np.nan)
                else:
                    rho = _pearson_on_ranks(ranks[ci], ranks[cj])
                mat[i, j] = rho
                mat[j, i] = rho
    return pd.DataFrame(mat, index=cols, columns=cols)
def redundant_pairs(matrix):
    pairs = []
    cols = list(matrix.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            rho = matrix.iloc[i, j]
            if abs(rho) > REDUNDANCY_THRESHOLD:
                pairs.append((cols[i], cols[j], rho))
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    return pairs
def log_hist(df):
    fi = df["fan_in"].values
    mask_fi = fi > 0
    h_fi, _ = np.histogram(np.log10(fi[mask_fi]), bins=HIST_BINS)
    fe = df["fan_in_external"].values
    mask_fe = fe > 0
    h_fe, _ = np.histogram(np.log10(fe[mask_fe]), bins=HIST_BINS)
    return h_fi, h_fe
# ── Per-dataset orchestrator ──────────────────────────────────────────
def analyze_dataset(label, path):
    print(f"\n=== Dataset: {label} ===")
    print(f"  loading {path.name}...")
    df = load_dataset(path)
    if label == EXTERNAL:
        # Same population as A; fan-in counts only dependents from other scopes
        df["fan_in"] = df["fan_in_external"]
    n = len(df)
    print(f"  {n:,} packages")
    print(f"  step 1: zeros grid")
    zg = zeros_grid(df)
    print(f"  step 2: variable stats")
    vs = variable_stats(df)
    print(f"  step 3: tramo table")
    tt = tramo_table(df)
    print(f"  step 4: check fan_in_internal")
    chk = check_internal(df)
    if label == "sin familias" and chk > 0:
        print(f"  WARNING: {chk} packages with fan_in_internal > 0 in dataset B")
    print(f"  step 5: Spearman")
    sp_in, sp_out = spearman_tables(df, label)
    print(f"  step 6: correlation matrix")
    cm = corr_matrix(df)
    print(f"  step 7: redundant pairs")
    rp = redundant_pairs(cm)
    print(f"  step 8: log histograms")
    h_fi, h_fe = log_hist(df)
    # rho of n_versions vs fan_in (all) for comparison table
    rho_nv_fi = float(sp_in.loc["n_versions", "all"])
    # fan_in stats for comparison table
    fi = df["fan_in"].values
    pct_fi0 = (fi == 0).mean() * 100
    med_fi = float(np.median(fi))
    p99_fi = float(np.percentile(fi, 99))
    # internal share (only meaningful for A)
    sum_fi = int(fi.sum())
    sum_fi_int = int(df["fan_in_internal"].sum())
    pct_int_share = sum_fi_int / sum_fi * 100 if sum_fi > 0 else 0.0
    pct_has_int = (df["fan_in_internal"] > 0).mean() * 100
    result = {
        "n": n, "zeros": zg, "stats": vs,
        "sp_in": sp_in, "sp_out": sp_out,
        "corr": cm, "pairs": rp, "tramos": tt,
        "check": chk, "hist_fi": h_fi, "hist_fe": h_fe,
        "rho_nv_fi": rho_nv_fi,
        "pct_fi0": pct_fi0, "med_fi": med_fi, "p99_fi": p99_fi,
        "sum_fi": sum_fi, "sum_fi_int": sum_fi_int,
        "pct_int_share": pct_int_share, "pct_has_int": pct_has_int,
        "label": label,
    }
    del df
    gc.collect()
    return result
# ── Formatting ────────────────────────────────────────────────────────
def format_number(v, decimals=0):
    # Spanish thousands (dot) and decimal (comma).
    try:
        if np.isnan(v):
            return "—"
    except (TypeError, ValueError):
        pass
    if decimals == 0:
        return f"{int(v):,}".replace(",", ".")
    s = f"{v:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")
def format_pct(v):
    try:
        if np.isnan(v):
            return "—"
    except (TypeError, ValueError):
        pass
    return format_number(v, decimals=1) + " %"
def _frho(v):
    try:
        if np.isnan(v):
            return "—"
    except (TypeError, ValueError):
        pass
    s = f"{v:+.3f}"
    return s.replace(".", ",")
# ── Comparison ────────────────────────────────────────────────────────
def compare(res):
    ra = res["con familias"]
    labels = [label for label, _ in DATASETS]
    summary = [
        ("N", [res[l]["n"] for l in labels]),
        ("% fan_in=0", [res[l]["pct_fi0"] for l in labels]),
        ("Mediana fan_in", [res[l]["med_fi"] for l in labels]),
        ("p99 fan_in", [res[l]["p99_fi"] for l in labels]),
        ("ρ(n_versions, fan_in)", [res[l]["rho_nv_fi"] for l in labels]),
        ("ρ(file_count, fan_in)",
         [float(res[l]["sp_in"].loc["file_count", "all"]) for l in labels]),
    ]
    ta = ra["tramos"]
    by_tramo = []
    for _, row in ta.iterrows():
        s_int = int(row["sum_fi_internal"])
        s_ext = int(row["sum_fi_external"])
        total = s_int + s_ext
        by_tramo.append((
            row["tramo"], s_int, s_ext,
            s_int / total * 100 if total > 0 else 0.0,
        ))
    return {
        "summary": summary,
        "pct_int_share": ra["pct_int_share"],
        "pct_has_int": ra["pct_has_int"],
        "by_tramo": by_tramo,
    }
# ── Figures ───────────────────────────────────────────────────────────
def _heatmap(ax, data, row_labels, col_labels, title):
    norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
    im = ax.imshow(data, cmap="RdBu_r", norm=norm, aspect="auto")
    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=7)
    ax.set_title(title, fontsize=9)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            text = "—" if np.isnan(data[i, j]) else f"{data[i, j]:.2f}"
            ax.text(j, i, text, ha="center", va="center",
                    fontsize=6, color="white" if abs(data[i, j]) > 0.6 else "black")
    return im
def fig_spearman_fan_in(res):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    vars_in = list(SPEARMAN_VARS) + ["fan_out"]
    col_labels, columns = [], []
    for label, _ in DATASETS:
        col_labels += [f"{SHORT[label]}\ntodos", f"{SHORT[label]}\nfan_in>0"]
        columns += [res[label]["sp_in"]["all"].values,
                    res[label]["sp_in"]["fan_in>0"].values]
    data = np.column_stack(columns)
    fig, ax = plt.subplots(figsize=(8, 6.5))
    im = _heatmap(ax, data, vars_in, col_labels, "Spearman ρ vs fan_in")
    fig.colorbar(im, ax=ax, shrink=0.6)
    fig.tight_layout()
    path = FIG_DIR / "fig1_spearman_fan_in.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
def fig_spearman_fan_out(res):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    vars_out = list(SPEARMAN_VARS) + ["fan_in"]
    col_labels, columns = [], []
    for label, _ in DATASETS:
        col_labels += [f"{SHORT[label]}\ntodos", f"{SHORT[label]}\nfan_out>0"]
        columns += [res[label]["sp_out"]["all"].values,
                    res[label]["sp_out"]["fan_out>0"].values]
    data = np.column_stack(columns)
    fig, ax = plt.subplots(figsize=(8, 6.5))
    im = _heatmap(ax, data, vars_out, col_labels, "Spearman ρ vs fan_out")
    fig.colorbar(im, ax=ax, shrink=0.6)
    fig.tight_layout()
    path = FIG_DIR / "fig2_spearman_fan_out.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
def fig_spearman_compare(res):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    vars_in = list(SPEARMAN_VARS) + ["fan_out"]
    x = np.arange(len(vars_in))
    w = 0.27
    fig, ax = plt.subplots(figsize=(9, 4))
    for k, (label, _) in enumerate(DATASETS):
        rho = [res[label]["sp_in"].loc[v, "all"] for v in vars_in]
        ax.bar(x + (k - 1) * w, rho, w, label=SHORT[label])
    ax.set_xticks(x)
    ax.set_xticklabels(vars_in, rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("ρ Spearman con fan_in")
    ax.set_title("ρ vs fan_in (todos los paquetes)")
    ax.legend(fontsize=8)
    ax.axhline(0, color="grey", linewidth=0.5)
    fig.tight_layout()
    path = FIG_DIR / "fig3_spearman_A_vs_B.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
def fig_corr_matrices(res):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for label, _ in DATASETS:
        slug = SLUG[label]
        r = res[label]
        cm = r["corr"]
        cols = list(cm.columns)
        fig, ax = plt.subplots(figsize=(8, 7))
        im = _heatmap(ax, cm.values, cols, cols,
                      f"Matriz Spearman — {label}")
        fig.colorbar(im, ax=ax, shrink=0.6)
        fig.tight_layout()
        path = FIG_DIR / f"fig4_corr_matrix_{slug}.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        paths.append(path)
    return paths
def fig_fan_in_distribution(res):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ra, rb = res["con familias"], res["sin familias"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    # Left: % packages per tramo, grouped bars
    x = np.arange(len(TRAMO_LABELS))
    w = 0.27
    for k, (label, _) in enumerate(DATASETS):
        ax1.bar(x + (k - 1) * w, res[label]["tramos"]["pct"].values, w,
                label=SHORT[label])
    ax1.set_xticks(x)
    ax1.set_xticklabels(TRAMO_LABELS, fontsize=8)
    ax1.set_ylabel("% de paquetes")
    ax1.set_xlabel("Tramo de fan_in")
    ax1.set_title("Distribución por tramo")
    ax1.legend(fontsize=7)
    # Right: histogram of log10(fan_in) for fan_in > 0
    centers = (HIST_BINS[:-1] + HIST_BINS[1:]) / 2
    bw = 0.08
    ax2.bar(centers - bw, ra["hist_fi"], width=bw, alpha=0.7,
            label="fan_in — con familias")
    ax2.bar(centers, rb["hist_fi"], width=bw, alpha=0.7,
            label="fan_in — sin familias")
    ax2.bar(centers + bw, ra["hist_fe"], width=bw, alpha=0.5,
            label="fan_in_external — con familias")
    ax2.set_xlabel("log₁₀(fan_in)")
    ax2.set_ylabel("N paquetes")
    ax2.set_title("Histograma log₁₀(fan_in), solo > 0")
    ax2.legend(fontsize=6)
    fig.tight_layout()
    path = FIG_DIR / "fig5_fan_in_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
def fig_by_tramo(res):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    x = np.arange(len(TRAMO_LABELS))
    panels = [
        (axes[0, 0], "med_n_versions", "Mediana de n_versions"),
        (axes[0, 1], "med_age_years", "Mediana de age_years"),
        (axes[1, 0], "pct_github", "% con GitHub"),
        (axes[1, 1], "pct_scoped", "% con scope"),
    ]
    for ax, col, title in panels:
        for (label, _), style in zip(DATASETS, ["o-", "^:", "s--"]):
            ax.plot(x, res[label]["tramos"][col].values, style, label=SHORT[label])
        ax.set_xticks(x)
        ax.set_xticklabels(TRAMO_LABELS, fontsize=8)
        ax.set_title(title, fontsize=9)
        ax.legend(fontsize=7)
    fig.suptitle("Por tramo de fan_in", fontsize=11)
    fig.tight_layout()
    path = FIG_DIR / "fig6_by_fan_in_tramo.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
def fig_internal_share(res):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ra = res["con familias"]
    ta = ra["tramos"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    x = np.arange(len(TRAMO_LABELS))
    ax1.bar(x, ta["sum_fi_internal"].values, label="Interno")
    ax1.bar(x, ta["sum_fi_external"].values,
            bottom=ta["sum_fi_internal"].values, label="Externo")
    ax1.set_xticks(x)
    ax1.set_xticklabels(TRAMO_LABELS, fontsize=8)
    ax1.set_ylabel("Σ fan_in")
    ax1.set_title("fan_in interno vs externo — con familias")
    ax1.legend(fontsize=7)
    ax2.bar(x, ta["pct_fi_internal_gt0"].values)
    ax2.set_xticks(x)
    ax2.set_xticklabels(TRAMO_LABELS, fontsize=8)
    ax2.set_ylabel("% paquetes")
    ax2.set_title("% con fan_in_internal > 0 — con familias")
    fig.tight_layout()
    path = FIG_DIR / "fig7_internal_share_con_familias.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
# ── Markdown report ───────────────────────────────────────────────────
FIGURES = [
    ("fig1_spearman_fan_in.png", "ρ Spearman vs fan_in"),
    ("fig2_spearman_fan_out.png", "ρ Spearman vs fan_out"),
    ("fig3_spearman_A_vs_B.png", "ρ vs fan_in en las tres situaciones"),
    ("fig4_corr_matrix_con_familias.png", "Matriz Spearman — con familias"),
    ("fig4_corr_matrix_fan_in_externo.png", "Matriz Spearman — Fan-In externo"),
    ("fig4_corr_matrix_sin_familias.png", "Matriz Spearman — sin familias"),
    ("fig5_fan_in_distribution.png", "Distribución de fan_in"),
    ("fig6_by_fan_in_tramo.png", "Variables por tramo de fan_in"),
    ("fig7_internal_share_con_familias.png", "fan_in interno (solo con familias)"),
]
def _write_dataset(f, r):
    label = r["label"]
    fn, fp, fr = format_number, format_pct, _frho
    f.write(f"# Dataset: {label}\n\n")
    if label == EXTERNAL:
        f.write("Población A, con fan_in contado solo desde otros scopes "
                "(fan_in_external).\n\n")
    # 1
    f.write("## 1. Tamaño y ceros\n\n")
    f.write(f"Paquetes: {fn(r['n'])}\n\n")
    f.write("| Celda | N | % |\n|-------|---|---|\n")
    for lbl, cnt, pct in r["zeros"]:
        f.write(f"| {lbl} | {fn(cnt)} | {fp(pct)} |\n")
    f.write("\n")
    # 2
    f.write("## 2. Estadísticos por variable\n\n")
    f.write("% cero y los percentiles se calculan sobre los valores presentes.\n\n")
    f.write("| Variable | % faltante | % cero | Mediana | p90 | p99 | Máx |\n")
    f.write("|----------|------------|--------|---------|-----|-----|-----|\n")
    for _, row in r["stats"].iterrows():
        v = row["variable"]
        if v in ("has_github", "deprecated", "scoped"):
            continue
        f.write(f"| {v} | {fp(row['pct_missing'])} | {fp(row['pct_zero'])} "
                f"| {fn(row['median'], 1)} "
                f"| {fn(row['p90'], 1)} | {fn(row['p99'], 1)} "
                f"| {fn(row['max'])} |\n")
    f.write("\n| Variable | % verdaderos |\n|----------|--------------|\n")
    for _, row in r["stats"].iterrows():
        pt = row.get("pct_true", np.nan)
        try:
            is_nan = np.isnan(pt)
        except (TypeError, ValueError):
            is_nan = False
        if not is_nan:
            f.write(f"| {row['variable']} | {fp(pt)} |\n")
    f.write("\n")
    # 3
    f.write("## 3. Spearman vs fan_in\n\n")
    f.write("| Variable | Todos | fan_in > 0 |\n|----------|-------|------------|\n")
    for v in r["sp_in"].index:
        f.write(f"| {v} | {fr(r['sp_in'].loc[v, 'all'])} "
                f"| {fr(r['sp_in'].loc[v, 'fan_in>0'])} |\n")
    f.write("\n")
    # 4
    f.write("## 4. Spearman vs fan_out\n\n")
    f.write("| Variable | Todos | fan_out > 0 |\n|----------|-------|-------------|\n")
    for v in r["sp_out"].index:
        f.write(f"| {v} | {fr(r['sp_out'].loc[v, 'all'])} "
                f"| {fr(r['sp_out'].loc[v, 'fan_out>0'])} |\n")
    f.write("\n")
    # 5
    f.write(f"## 5. Pares redundantes (|ρ| > {fn(REDUNDANCY_THRESHOLD, 1)})\n\n")
    if r["pairs"]:
        f.write("| Variable A | Variable B | ρ |\n|------------|------------|---|\n")
        for a, b, rho in r["pairs"]:
            f.write(f"| {a} | {b} | {fr(rho)} |\n")
    else:
        f.write("Ningún par supera el umbral.\n")
    f.write("\n")
    # 6
    f.write("## 6. Tabla por tramo de fan_in\n\n")
    f.write("| Tramo | N | % | Med n_versions | Med age_years | Med file_count "
            "| % GitHub | % scoped | % deprecated "
            "| Σ fi_internal | Σ fi_external | % fi_internal>0 |\n")
    f.write("|-------|---|---|----------------|---------------|----------------"
            "|----------|----------|-------------"
            "|---------------|---------------|------------------|\n")
    for _, row in r["tramos"].iterrows():
        f.write(f"| {row['tramo']} | {fn(row['n'])} "
                f"| {fp(row['pct'])} "
                f"| {fn(row['med_n_versions'], 1)} "
                f"| {fn(row['med_age_years'], 1)} "
                f"| {fn(row['med_file_count'], 1)} "
                f"| {fp(row['pct_github'])} "
                f"| {fp(row['pct_scoped'])} "
                f"| {fp(row['pct_deprecated'])} "
                f"| {fn(row['sum_fi_internal'])} "
                f"| {fn(row['sum_fi_external'])} "
                f"| {fp(row['pct_fi_internal_gt0'])} |\n")
    f.write("\n")
    # 7
    if label == "sin familias":
        f.write("## 7. Comprobación (solo dataset sin familias)\n\n")
        f.write(f"Paquetes con fan_in_internal > 0: {fn(r['check'])}\n\n")
        if r["check"] > 0:
            f.write("**AVISO:** se esperaba 0.\n\n")
def write_md(res, comp):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fn, fp, fr = format_number, format_pct, _frho
    with open(OUT_DIR / "descriptive_stats.md", "w", encoding="utf-8") as f:
        for label, _ in DATASETS:
            _write_dataset(f, res[label])
        # Comparison
        f.write("# Comparación entre datasets\n\n")
        f.write("| Métrica | " + " | ".join(SHORT[l] for l, _ in DATASETS) + " |\n")
        f.write("|---------|" + "---|" * len(DATASETS) + "\n")
        for name, values in comp["summary"]:
            if name == "N":
                cells = [fn(v) for v in values]
            elif name.startswith("%"):
                cells = [fp(v) for v in values]
            elif name.startswith("ρ"):
                cells = [fr(v) for v in values]
            else:
                cells = [fn(v, 1) for v in values]
            f.write(f"| {name} | " + " | ".join(cells) + " |\n")
        f.write("\n### Solo con familias: fan_in interno\n\n")
        f.write(f"- Parte interna del fan_in total: {fp(comp['pct_int_share'])}\n")
        f.write(f"- Paquetes con fan_in_internal > 0: {fp(comp['pct_has_int'])}\n\n")
        f.write("| Tramo | Σ fi_internal | Σ fi_external | % interno |\n")
        f.write("|-------|---------------|---------------|----------|\n")
        for tramo, s_int, s_ext, pct_i in comp["by_tramo"]:
            f.write(f"| {tramo} | {fn(s_int)} | {fn(s_ext)} | {fp(pct_i)} |\n")
        f.write("\n")
        # Figures
        f.write("# Gráficos\n\n")
        for name, caption in FIGURES:
            f.write(f"### {caption}\n\n![{caption}](figures/{name})\n\n")
# ── Main ──────────────────────────────────────────────────────────────
def main():
    print("08_descriptive_stats.py")
    res = {}
    for label, fname in DATASETS:
        print(f"\n--- {label} ---")
        res[label] = analyze_dataset(label, DATA_DIR / fname)
    comp = compare(res)
    print("\nGenerating figures...")
    fig_spearman_fan_in(res);    print("  fig1 done")
    fig_spearman_fan_out(res);   print("  fig2 done")
    fig_spearman_compare(res);   print("  fig3 done")
    fig_corr_matrices(res);      print("  fig4 done")
    fig_fan_in_distribution(res); print("  fig5 done")
    fig_by_tramo(res);           print("  fig6 done")
    fig_internal_share(res);     print("  fig7 done")
    print("Writing markdown...")
    write_md(res, comp)
    # Console comparison
    print("\n=== Comparación de las tres situaciones ===")
    print(f"  {'':25s}  {'Con fam':>12s}  {'Externo':>12s}  {'Sin fam':>12s}")
    for name, values in comp["summary"]:
        if name == "N":
            cells = [f"{v:>12,}" for v in values]
        elif name.startswith("%"):
            cells = [f"{v:>11.1f}%" for v in values]
        elif name.startswith("ρ"):
            cells = [f"{v:>+12.3f}" for v in values]
        else:
            cells = [f"{v:>12.1f}" for v in values]
        print(f"  {name:25s}  " + "  ".join(cells))
    print(f"\n  Con familias: parte interna = {comp['pct_int_share']:.1f}%")
    print(f"  Con familias: paquetes con fi_internal>0 = {comp['pct_has_int']:.1f}%")
    print("\nDone.")
if __name__ == "__main__":
    main()