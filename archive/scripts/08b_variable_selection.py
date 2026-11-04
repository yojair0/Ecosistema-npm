# 08b_variable_selection.py -- Step 1: descriptives and family analysis.
# Compares three groups of npm packages to measure which external
# variables are useful for stratification by Fan-In and Fan-Out.
import gc
from datetime import date
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, TwoSlopeNorm
import numpy as np
import pandas as pd
from scipy.stats import rankdata

# ── Constants ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "07_inclusion_packages"
PARQUET_A = DATA_DIR / "population_with_families.parquet"
PARQUET_B = DATA_DIR / "population_without_families.parquet"
SNAPSHOT_DATE = date(2026, 9, 18)
FAMILY_MIN_SIZE = 2
PARQUET_COLS = [
    "fan_in", "fan_in_internal", "fan_in_external",
    "fan_out", "fan_out_internal", "fan_out_external",
    "fan_in_dev", "fan_out_dev",
    "n_versions", "n_maintainers", "n_keywords", "n_peer", "n_opt",
    "created_date", "has_github", "deprecated", "scope", "scope_size",
]
VARS = [
    "n_versions", "n_maintainers", "n_keywords", "n_peer", "n_opt",
    "age_years", "has_github", "deprecated", "scoped",
    "fan_in_dev", "fan_out_dev",
]
BINARY_VARS = {"has_github", "deprecated", "scoped"}
NUMERIC_VARS = [v for v in VARS if v not in BINARY_VARS]
GROUP_DEFS = [
    ("A: con familias", "fan_in", "fan_out"),
    ("A externo: mismos paquetes, solo vinculos externos",
     "fan_in_external", "fan_out_external"),
    ("B: sin familias", "fan_in", "fan_out"),
]
FI_EDGES = [(0, 0), (1, 9), (10, 99), (100, 999), (1000, None)]
FI_LABELS = ["0", "1-9", "10-99", "100-999", "1000+"]
FO_EDGES = [(0, 0), (1, 2), (3, 9), (10, 49), (50, None)]
FO_LABELS = ["0", "1-2", "3-9", "10-49", "50+"]
ZERO_CELLS = [
    ("Aislado (Fan-In 0, Fan-Out 0)", True, True),
    ("Consumidor (Fan-In 0, Fan-Out mayor a 0)", True, False),
    ("Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0)", False, True),
    ("Con ambas conexiones", False, False),
]
ZERO_NAMES = [name for name, _, _ in ZERO_CELLS]
PROFILE_MED_COLS = ["n_versions", "n_maintainers", "n_keywords", "age_years"]
PROFILE_PCT_COLS = ["has_github", "scoped", "deprecated"]
PROFILE_GT0_COLS = ["fan_in_dev", "fan_out_dev"]
FIG_DIR = ROOT / "data" / "08b_variable_selection" / "figures"
GROUP_LABELS = [g[0] for g in GROUP_DEFS]
GROUP_SHORT = ["A", "A ext", "B"]

# ── Data loading ─────────────────────────────────────────────────────
def load_parquet(path):
    df = pd.read_parquet(str(path), columns=PARQUET_COLS)
    days = (pd.Timestamp(SNAPSHOT_DATE) - pd.to_datetime(df["created_date"])).dt.days
    df["age_years"] = (days / 365.25).astype("float32")
    df["creation_year"] = pd.to_datetime(df["created_date"]).dt.year.astype("Int16")
    df.drop(columns=["created_date"], inplace=True)
    df["scoped"] = (df["scope"].fillna("").astype(str) != "").astype("int8")
    df["family"] = (df["scope_size"].fillna(0) >= FAMILY_MIN_SIZE).astype("int8")
    df.drop(columns=["scope", "scope_size"], inplace=True)
    for col in ("has_github", "deprecated"):
        df[col] = df[col].fillna(0).astype(bool).astype("int8")
    for col in ("fan_in", "fan_in_internal", "fan_in_external",
                "fan_out", "fan_out_internal", "fan_out_external",
                "fan_in_dev", "fan_out_dev",
                "n_versions", "n_maintainers", "n_keywords",
                "n_peer", "n_opt"):
        df[col] = df[col].fillna(0).astype("int32")
    return df

# ── Tramo and zero-cell helpers ──────────────────────────────────────
def assign_tramo(values, edges, labels):
    arr = np.asarray(values)
    result = np.empty(len(arr), dtype=object)
    for (lo, hi), label in zip(edges, labels):
        if hi is None:
            mask = arr >= lo
        else:
            mask = (arr >= lo) & (arr <= hi)
        result[mask] = label
    return pd.Categorical(result, categories=labels, ordered=True)
def assign_fi_tramo(fi):
    return assign_tramo(fi, FI_EDGES, FI_LABELS)
def assign_fo_tramo(fo):
    return assign_tramo(fo, FO_EDGES, FO_LABELS)
def assign_zero_cell(fi, fo):
    fi0 = np.asarray(fi) == 0
    fo0 = np.asarray(fo) == 0
    result = np.empty(len(fi0), dtype=object)
    for name, is_fi0, is_fo0 in ZERO_CELLS:
        result[(fi0 == is_fi0) & (fo0 == is_fo0)] = name
    return pd.Categorical(result, categories=ZERO_NAMES, ordered=True)

# ── Per-group computations ───────────────────────────────────────────
def compute_zeros(fi, fo, n):
    fi0 = np.asarray(fi) == 0
    fo0 = np.asarray(fo) == 0
    rows = []
    for name, is_fi0, is_fo0 in ZERO_CELLS:
        cnt = int(((fi0 == is_fi0) & (fo0 == is_fo0)).sum())
        rows.append({"cell": name, "n": cnt, "pct": cnt / n * 100})
    return rows
def compute_joint_grid(fi_tramo, fo_tramo):
    return pd.crosstab(fi_tramo, fo_tramo, dropna=False)
def compute_var_stats(df, fi, fo):
    rows = []
    for label, values in [("fi", fi), ("fo", fo)]:
        a = np.asarray(values, dtype="float64")
        rows.append({
            "variable": label, "pct_zero": (a == 0).mean() * 100,
            "median": float(np.median(a)), "p90": float(np.percentile(a, 90)),
            "p99": float(np.percentile(a, 99)), "max": float(a.max()),
        })
    for v in NUMERIC_VARS:
        a = df[v].values.astype("float64")
        rows.append({
            "variable": v, "pct_zero": (a == 0).mean() * 100,
            "median": float(np.median(a)), "p90": float(np.percentile(a, 90)),
            "p99": float(np.percentile(a, 99)), "max": float(a.max()),
        })
    for v in VARS:
        if v in BINARY_VARS:
            rows.append({
                "variable": v,
                "pct_true": df[v].values.astype("float64").mean() * 100,
            })
    return rows
def _profile_row(sub, n_total):
    cnt = len(sub)
    if cnt == 0:
        return {"n": 0, "pct": 0.0}
    row = {"n": cnt, "pct": cnt / n_total * 100}
    for col in PROFILE_MED_COLS:
        row[f"med_{col}"] = float(np.median(sub[col].values))
    for col in PROFILE_PCT_COLS:
        row[f"pct_{col}"] = sub[col].values.astype("float64").mean() * 100
    for col in PROFILE_GT0_COLS:
        row[f"pct_{col}_gt0"] = (sub[col].values > 0).mean() * 100
    return row
def profile_by(df, grouping, labels, n_total):
    rows = []
    for label in labels:
        sub = df[grouping == label]
        row = _profile_row(sub, n_total)
        row["level"] = label
        rows.append(row)
    return rows
def analyze_group(df, fi_col, fo_col, label):
    n = len(df)
    fi = df[fi_col].values
    fo = df[fo_col].values
    fi_tramo = assign_fi_tramo(fi)
    fo_tramo = assign_fo_tramo(fo)
    zero_cell = assign_zero_cell(fi, fo)
    print(f"  {label}: {n:,} packages")
    return {
        "label": label, "n": n,
        "zeros": compute_zeros(fi, fo, n),
        "joint_grid": compute_joint_grid(fi_tramo, fo_tramo),
        "var_stats": compute_var_stats(df, fi, fo),
        "profile_fi": profile_by(df, fi_tramo, FI_LABELS, n),
        "profile_fo": profile_by(df, fo_tramo, FO_LABELS, n),
        "profile_zeros": profile_by(df, zero_cell, ZERO_NAMES, n),
    }

# ── Family analysis (group A only) ──────────────────────────────────
def _ie_rows(df, metric_col, internal_col, edges, labels):
    arr = df[metric_col].values
    tramo = assign_tramo(arr, edges, labels)
    int_arr = df[internal_col].values
    rows = []
    for label in labels:
        mask = np.asarray(tramo == label)
        s_m = int(arr[mask].sum())
        s_i = int(int_arr[mask].sum())
        rows.append({
            "tramo": label, "sum_internal": s_i,
            "sum_external": s_m - s_i,
            "pct_internal": s_i / s_m * 100 if s_m > 0 else 0.0,
        })
    s_m = int(arr.sum())
    s_i = int(int_arr.sum())
    rows.append({
        "tramo": "Total", "sum_internal": s_i,
        "sum_external": s_m - s_i,
        "pct_internal": s_i / s_m * 100 if s_m > 0 else 0.0,
    })
    return rows
def family_internal_external(df):
    return {
        "fan_in": _ie_rows(df, "fan_in", "fan_in_internal",
                           FI_EDGES, FI_LABELS),
        "fan_out": _ie_rows(df, "fan_out", "fan_out_internal",
                            FO_EDGES, FO_LABELS),
    }
def family_stratum_change(df):
    fi_t = assign_fi_tramo(df["fan_in"].values)
    fi_e = assign_fi_tramo(df["fan_in_external"].values)
    fo_t = assign_fo_tramo(df["fan_out"].values)
    fo_e = assign_fo_tramo(df["fan_out_external"].values)
    zc_t = assign_zero_cell(df["fan_in"].values, df["fan_out"].values)
    zc_e = assign_zero_cell(df["fan_in_external"].values,
                            df["fan_out_external"].values)
    fi_same = np.asarray(fi_t) == np.asarray(fi_e)
    fo_same = np.asarray(fo_t) == np.asarray(fo_e)
    n = len(df)
    nc = int((fi_same & fo_same).sum())
    fi_o = int((~fi_same & fo_same).sum())
    fo_o = int((fi_same & ~fo_same).sum())
    bt = int((~fi_same & ~fo_same).sum())
    return {
        "xt_fi": pd.crosstab(fi_t, fi_e, dropna=False),
        "xt_fo": pd.crosstab(fo_t, fo_e, dropna=False),
        "xt_zero": pd.crosstab(zc_t, zc_e, dropna=False),
        "summary": [
            {"change": "no_change", "n": nc, "pct": nc / n * 100},
            {"change": "fi_only", "n": fi_o, "pct": fi_o / n * 100},
            {"change": "fo_only", "n": fo_o, "pct": fo_o / n * 100},
            {"change": "both", "n": bt, "pct": bt / n * 100},
        ],
    }
def _retention_rows(stays, grouping, labels):
    rows = []
    for label in labels:
        mask = np.asarray(grouping == label)
        n_a = int(mask.sum())
        n_ret = int((mask & stays).sum())
        rows.append({
            "level": label, "n_a": n_a, "n_retained": n_ret,
            "pct": n_ret / n_a * 100 if n_a > 0 else 0.0,
        })
    return rows
def family_retention(df):
    stays = (df["family"] == 0).values
    fi = df["fan_in"].values
    fo = df["fan_out"].values
    fi_tr = assign_fi_tramo(fi)
    fo_tr = assign_fo_tramo(fo)
    zc = assign_zero_cell(fi, fo)
    # joint grid
    joint = []
    for fi_l in FI_LABELS:
        for fo_l in FO_LABELS:
            mask = np.asarray(fi_tr == fi_l) & np.asarray(fo_tr == fo_l)
            n_a = int(mask.sum())
            n_ret = int((mask & stays).sum())
            joint.append({
                "fi_tramo": fi_l, "fo_tramo": fo_l,
                "n_a": n_a, "n_retained": n_ret,
                "pct": n_ret / n_a * 100 if n_a > 0 else 0.0,
            })
    result = {
        "joint_grid": joint,
        "fi_tramo": _retention_rows(stays, fi_tr, FI_LABELS),
        "fo_tramo": _retention_rows(stays, fo_tr, FO_LABELS),
        "zero_cell": _retention_rows(stays, zc, ZERO_NAMES),
    }
    # by creation year
    years = sorted(df["creation_year"].dropna().unique())
    yr_rows = []
    for yr in years:
        mask = (df["creation_year"] == yr).values
        n_a = int(mask.sum())
        n_ret = int((mask & stays).sum())
        yr_rows.append({
            "level": int(yr), "n_a": n_a, "n_retained": n_ret,
            "pct": n_ret / n_a * 100 if n_a > 0 else 0.0,
        })
    result["creation_year"] = yr_rows
    # by scoped
    sc_rows = []
    for val, label in [(1, "scoped"), (0, "unscoped")]:
        mask = (df["scoped"] == val).values
        n_a = int(mask.sum())
        n_ret = int((mask & stays).sum())
        sc_rows.append({
            "level": label, "n_a": n_a, "n_retained": n_ret,
            "pct": n_ret / n_a * 100 if n_a > 0 else 0.0,
        })
    result["scoped"] = sc_rows
    return result
def _ls_row(sub, fi_arr, fo_arr):
    n = len(sub)
    if n == 0:
        return {"n": 0}
    result = {"n": n}
    result["med_n_versions"] = float(np.median(sub["n_versions"].values))
    result["med_n_maintainers"] = float(np.median(sub["n_maintainers"].values))
    result["med_age_years"] = float(np.median(sub["age_years"].values))
    for v in ("n_keywords", "n_peer", "n_opt", "fan_in_dev", "fan_out_dev"):
        result[f"pct_nonzero_{v}"] = (sub[v].values > 0).mean() * 100
    result["pct_fi_gt0"] = (fi_arr > 0).mean() * 100
    result["p90_fi"] = float(np.percentile(fi_arr, 90))
    result["p99_fi"] = float(np.percentile(fi_arr, 99))
    result["pct_fo_gt0"] = (fo_arr > 0).mean() * 100
    result["p90_fo"] = float(np.percentile(fo_arr, 90))
    result["p99_fo"] = float(np.percentile(fo_arr, 99))
    for v in ("has_github", "deprecated", "scoped"):
        result[f"pct_{v}"] = sub[v].values.astype("float64").mean() * 100
    fi_tr = assign_fi_tramo(fi_arr)
    fo_tr = assign_fo_tramo(fo_arr)
    zc = assign_zero_cell(fi_arr, fo_arr)
    result["by_zero_cell"] = {
        name: float((zc == name).mean() * 100) for name in ZERO_NAMES}
    result["by_fi_tramo"] = {
        label: float((fi_tr == label).mean() * 100) for label in FI_LABELS}
    result["by_fo_tramo"] = {
        label: float((fo_tr == label).mean() * 100) for label in FO_LABELS}
    return result
def family_leavers_stayers(df):
    leavers = df[df["family"] == 1]
    stayers = df[df["family"] == 0]
    return {
        "leavers": _ls_row(
            leavers, leavers["fan_in"].values, leavers["fan_out"].values),
        "stayers": _ls_row(
            stayers, stayers["fan_in"].values, stayers["fan_out"].values),
        "note_scoped_leavers": "scoped is 100% for leavers by definition",
    }
def analyze_families(df):
    print("  internal/external split ...")
    ie = family_internal_external(df)
    print("  stratum change A -> A_ext ...")
    sc = family_stratum_change(df)
    print("  retention A -> B ...")
    ret = family_retention(df)
    print("  leavers vs stayers ...")
    ls = family_leavers_stayers(df)
    return {
        "internal_external": ie,
        "stratum_change": sc,
        "retention": ret,
        "leavers_stayers": ls,
    }

# ── Step 2: measures for variable selection ──────────────────────────
REDUNDANCY_THRESHOLD = 0.7
MODEL_SAMPLE = 300_000
MODEL_MAX_TEST = 100_000
SEED = 42
def _pearson_on_ranks(rx, ry):
    mx, my = rx.mean(), ry.mean()
    dx, dy = rx - mx, ry - my
    den = np.sqrt((dx * dx).sum() * (dy * dy).sum())
    if den == 0:
        return np.nan
    return float((dx * dy).sum() / den)
def compute_spearman(df, fi_col, fo_col):
    arrs = {"fi": df[fi_col].values.astype("float64"),
            "fo": df[fo_col].values.astype("float64")}
    for v in VARS:
        arrs[v] = df[v].values.astype("float64")
    ranks_all = {k: rankdata(a, method="average") for k, a in arrs.items()}
    def _block(target, var_list, pos_mask):
        out_all = {v: _pearson_on_ranks(ranks_all[target], ranks_all[v])
                   for v in var_list}
        if int(pos_mask.sum()) < 3:
            out_pos = {v: np.nan for v in var_list}
        else:
            r_pos = {k: rankdata(arrs[k][pos_mask], method="average")
                     for k in [target] + var_list}
            out_pos = {v: _pearson_on_ranks(r_pos[target], r_pos[v])
                       for v in var_list}
        return out_all, out_pos
    vars_fi = list(VARS) + ["fo"]
    all_fi, pos_fi = _block("fi", vars_fi, arrs["fi"] > 0)
    print("    fi done")
    vars_fo = list(VARS) + ["fi"]
    all_fo, pos_fo = _block("fo", vars_fo, arrs["fo"] > 0)
    print("    fo done")
    return {
        "sp_fi": pd.DataFrame({"all": all_fi, "fi>0": pos_fi}),
        "sp_fo": pd.DataFrame({"all": all_fo, "fo>0": pos_fo}),
    }
def compute_fi_fo_rho(fi, fo):
    fi_f = fi.astype("float64")
    fo_f = fo.astype("float64")
    rho_all = _pearson_on_ranks(rankdata(fi_f, method="average"),
                                rankdata(fo_f, method="average"))
    both = (fi > 0) & (fo > 0)
    if both.sum() < 3:
        rho_both = np.nan
    else:
        rho_both = _pearson_on_ranks(rankdata(fi_f[both], method="average"),
                                     rankdata(fo_f[both], method="average"))
    return {"all": rho_all, "both_gt0": rho_both}
def compute_corr_matrix(df, fi_col, fo_col):
    col_names = ["fi", "fo"] + list(VARS)
    arrs = {"fi": df[fi_col].values.astype("float64"),
            "fo": df[fo_col].values.astype("float64")}
    for v in VARS:
        arrs[v] = df[v].values.astype("float64")
    ranks = {c: rankdata(arrs[c], method="average") for c in col_names}
    nc = len(col_names)
    mat = np.ones((nc, nc))
    for i in range(nc):
        for j in range(i + 1, nc):
            rho = _pearson_on_ranks(ranks[col_names[i]], ranks[col_names[j]])
            mat[i, j] = rho
            mat[j, i] = rho
    return pd.DataFrame(mat, index=col_names, columns=col_names)
def _redundant_pairs(matrix):
    pairs = []
    cols = list(matrix.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            rho = matrix.iloc[i, j]
            if abs(rho) > REDUNDANCY_THRESHOLD:
                pairs.append((cols[i], cols[j], float(rho)))
    pairs.sort(key=lambda p: abs(p[2]), reverse=True)
    return pairs
def _auc_mannwhitney(target, x):
    pos = target > 0
    n1 = int(pos.sum())
    n0 = len(target) - n1
    if n0 == 0 or n1 == 0:
        return np.nan
    r = rankdata(x, method="average")
    u = r[pos].sum() - n1 * (n1 + 1) / 2.0
    return float(u / (n0 * n1))
def compute_auc_mw(df, fi_col, fo_col):
    targets = [("fi", df[fi_col].values.astype("float64")),
               ("fo", df[fo_col].values.astype("float64"))]
    rows = []
    for t_name, t_arr in targets:
        for v in VARS:
            x = df[v].values.astype("float64")
            rows.append({"target": t_name, "variable": v,
                         "auc": _auc_mannwhitney(t_arr, x)})
    return rows
def _kw_epsilon_sq(x, tramo, labels):
    N = len(x)
    if N < 3:
        return np.nan
    r = rankdata(x, method="average")
    grand = (N + 1) / 2.0
    ss = 0.0
    for label in labels:
        mask = np.asarray(tramo == label)
        nj = mask.sum()
        if nj == 0:
            continue
        ss += nj * (r[mask].mean() - grand) ** 2
    H = 12.0 * ss / (N * (N + 1))
    return float(H / (N - 1))
def _cramer_v(binary, tramo, labels):
    N = len(binary)
    if N == 0:
        return np.nan
    k = len(labels)
    ct = np.zeros((2, k))
    for j, label in enumerate(labels):
        mask = np.asarray(tramo == label)
        col = binary[mask]
        ct[0, j] = (col == 0).sum()
        ct[1, j] = (col == 1).sum()
    row_s = ct.sum(axis=1)
    col_s = ct.sum(axis=0)
    exp = np.outer(row_s, col_s) / N
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = float(np.where(exp > 0, (ct - exp) ** 2 / exp, 0.0).sum())
    denom = N * min(1, k - 1)
    if denom == 0:
        return np.nan
    return float(np.sqrt(chi2 / denom))
def compute_effect_sizes(df, fi_col, fo_col):
    targets = [("fi", df[fi_col].values, FI_EDGES, FI_LABELS),
               ("fo", df[fo_col].values, FO_EDGES, FO_LABELS)]
    rows = []
    for t_name, t_arr, edges, labels in targets:
        tramo = assign_tramo(t_arr, edges, labels)
        for v in VARS:
            x = df[v].values.astype("float64")
            if v in BINARY_VARS:
                val = _cramer_v(x.astype("int8"), tramo, labels)
                rows.append({"target": t_name, "variable": v,
                             "measure": "cramer_v", "value": val})
            else:
                val = _kw_epsilon_sq(x, tramo, labels)
                rows.append({"target": t_name, "variable": v,
                             "measure": "epsilon_sq", "value": val})
    return rows
def _nmi(x_bins, y_bins):
    n = len(x_bins)
    if n == 0:
        return np.nan
    y_u, y_inv = np.unique(y_bins, return_inverse=True)
    x_u, x_inv = np.unique(x_bins, return_inverse=True)
    ct = np.zeros((len(x_u), len(y_u)), dtype="float64")
    np.add.at(ct, (x_inv, y_inv), 1.0)
    pxy = ct / n
    px = pxy.sum(axis=1, keepdims=True)
    py = pxy.sum(axis=0, keepdims=True)
    nz = pxy > 0
    outer = px * py
    mi = float(np.sum(pxy[nz] * np.log(pxy[nz] / outer[nz])))
    py_f = py.ravel()
    hy = float(-np.sum(py_f[py_f > 0] * np.log(py_f[py_f > 0])))
    if hy == 0:
        return np.nan
    return mi / hy
def _discretize(x, q=10):
    try:
        return np.asarray(
            pd.qcut(x, q=q, labels=False, duplicates="drop"), dtype="int32")
    except (ValueError, TypeError):
        return np.zeros(len(x), dtype="int32")
def compute_nmi(df, fi_col, fo_col):
    targets = [("fi", df[fi_col].values, FI_EDGES, FI_LABELS),
               ("fo", df[fo_col].values, FO_EDGES, FO_LABELS)]
    rows = []
    for t_name, t_arr, edges, labels in targets:
        t_bins = np.asarray(assign_tramo(t_arr, edges, labels))
        for v in VARS:
            x = df[v].values.astype("float64")
            x_b = x.astype("int8") if v in BINARY_VARS else _discretize(x)
            rows.append({"target": t_name, "variable": v,
                         "nmi": _nmi(x_b, t_bins)})
    return rows
def compute_model_ceiling(df, fi_col, fo_col, parquet_path):
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.inspection import permutation_importance
        from sklearn.metrics import r2_score
        from sklearn.metrics import roc_auc_score
        from sklearn.model_selection import GroupShuffleSplit
    except ImportError:
        print("    scikit-learn not installed, skipping model ceiling")
        return None
    n = len(df)
    sample_n = min(MODEL_SAMPLE, n)
    rng = np.random.RandomState(SEED)
    idx = np.sort(rng.choice(n, size=sample_n, replace=False))
    scope = pd.read_parquet(str(parquet_path), columns=["scope"])["scope"]
    scope = scope.fillna("").astype(str).values
    sc = scope[idx].copy()
    empty = sc == ""
    sc[empty] = np.array(["_u" + str(i) for i in range(int(empty.sum()))])
    X = np.column_stack([df[v].values[idx].astype("float64") for v in VARS])
    results = {}
    for t_name, t_col in [("fi", fi_col), ("fo", fo_col)]:
        y_raw = df[t_col].values[idx].astype("float64")
        y_reg = np.log1p(y_raw)
        y_cls = (y_raw > 0).astype("int8")
        gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=SEED)
        tr, te = next(gss.split(X, y_reg, groups=sc))
        X_tr, X_te = X[tr], X[te]
        y_reg_tr, y_reg_te = y_reg[tr], y_reg[te]
        y_cls_tr, y_cls_te = y_cls[tr], y_cls[te]
        if len(te) > MODEL_MAX_TEST:
            pi_idx = rng.choice(len(te), size=MODEL_MAX_TEST, replace=False)
        else:
            pi_idx = np.arange(len(te))
        X_pi = X_te[pi_idx]
        y_reg_pi, y_cls_pi = y_reg_te[pi_idx], y_cls_te[pi_idx]
        reg = HistGradientBoostingRegressor(
            max_iter=200, learning_rate=0.1,
            early_stopping=False, random_state=SEED)
        reg.fit(X_tr, y_reg_tr)
        r2 = float(r2_score(y_reg_te, reg.predict(X_te)))
        pi_r = permutation_importance(
            reg, X_pi, y_reg_pi, n_repeats=3,
            scoring="r2", random_state=SEED)
        clf = HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.1,
            early_stopping=False, random_state=SEED)
        clf.fit(X_tr, y_cls_tr)
        proba = clf.predict_proba(X_te)[:, 1]
        auc = float(roc_auc_score(y_cls_te, proba))
        pi_c = permutation_importance(
            clf, X_pi, y_cls_pi, n_repeats=3,
            scoring="roc_auc", random_state=SEED)
        imp_r = {VARS[i]: float(pi_r.importances_mean[i])
                 for i in range(len(VARS))}
        imp_c = {VARS[i]: float(pi_c.importances_mean[i])
                 for i in range(len(VARS))}
        results[t_name] = {
            "r2": r2, "auc": auc,
            "imp_reg": imp_r, "imp_clf": imp_c,
            "top_reg": max(imp_r, key=imp_r.get),
            "top_clf": max(imp_c, key=imp_c.get),
        }
        print(f"    {t_name}: R2={r2:.3f}, AUC={auc:.3f}")
    return results
def analyze_measures(df, fi_col, fo_col, label, parquet_path):
    print(f"  [{label}] Spearman ...")
    sp = compute_spearman(df, fi_col, fo_col)
    print(f"  [{label}] fi-fo rho ...")
    fifo = compute_fi_fo_rho(df[fi_col].values, df[fo_col].values)
    print(f"  [{label}] correlation matrix ...")
    cm = compute_corr_matrix(df, fi_col, fo_col)
    rp = _redundant_pairs(cm)
    print(f"  [{label}] AUC (Mann-Whitney) ...")
    auc = compute_auc_mw(df, fi_col, fo_col)
    print(f"  [{label}] effect sizes ...")
    es = compute_effect_sizes(df, fi_col, fo_col)
    print(f"  [{label}] NMI ...")
    nmi = compute_nmi(df, fi_col, fo_col)
    print(f"  [{label}] model ceiling ...")
    model = compute_model_ceiling(df, fi_col, fo_col, parquet_path)
    return {
        "spearman": sp, "fi_fo_rho": fifo,
        "corr_matrix": cm, "redundant_pairs": rp,
        "auc_mw": auc, "effect_sizes": es,
        "nmi": nmi, "model": model,
    }

# ── Step 3: figures ──────────────────────────────────────────────────
def _ensure_fig_dir():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
def _draw_heatmap(ax, data, row_labels, col_labels, fmt=".0f",
                  cmap="YlOrRd", norm=None, vmin=None, vmax=None,
                  annot_size=8, empty_text="–", title=None, xlabel=None,
                  ylabel=None):
    nr, nc = data.shape
    im = ax.imshow(data, aspect="auto", cmap=cmap, norm=norm,
                   vmin=vmin, vmax=vmax)
    ax.set_xticks(range(nc))
    ax.set_xticklabels(col_labels, fontsize=7)
    ax.set_yticks(range(nr))
    ax.set_yticklabels(row_labels, fontsize=7)
    for i in range(nr):
        for j in range(nc):
            v = data[i, j]
            if np.isnan(v) or (norm is None and v == 0 and fmt == ".0f"):
                ax.text(j, i, empty_text, ha="center", va="center",
                        fontsize=annot_size, color="gray")
            else:
                color = "white" if v > (data[np.isfinite(data)].max() * 0.65) else "black"
                ax.text(j, i, f"{v:{fmt}}", ha="center", va="center",
                        fontsize=annot_size, color=color)
    if title:
        ax.set_title(title, fontsize=9)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=8)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=8)
    return im
def _rho_heatmap(ax, data, row_labels, col_labels, **kwargs):
    norm = TwoSlopeNorm(vcenter=0, vmin=-0.5, vmax=0.5)
    nr, nc = data.shape
    im = ax.imshow(data, aspect="auto", cmap="RdBu_r", norm=norm)
    ax.set_xticks(range(nc))
    ax.set_xticklabels(col_labels, fontsize=7, rotation=45, ha="right")
    ax.set_yticks(range(nr))
    ax.set_yticklabels(row_labels, fontsize=7)
    for i in range(nr):
        for j in range(nc):
            v = data[i, j]
            if np.isnan(v):
                ax.text(j, i, "–", ha="center", va="center",
                        fontsize=7, color="gray")
            else:
                color = "white" if abs(v) > 0.35 else "black"
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=7, color=color)
    return im

def fig01_joint_grid(groups):
    _ensure_fig_dir()
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    for ax, lbl in zip(axes, GROUP_LABELS):
        g = groups[lbl]
        grid = g["joint_grid"].values.astype("float64")
        grid_log = np.where(grid > 0, grid, np.nan)
        norm = LogNorm(vmin=1, vmax=np.nanmax(grid_log))
        im = ax.imshow(grid_log, aspect="auto", cmap="YlOrRd", norm=norm)
        ax.set_xticks(range(len(FO_LABELS)))
        ax.set_xticklabels(FO_LABELS, fontsize=7)
        ax.set_yticks(range(len(FI_LABELS)))
        ax.set_yticklabels(FI_LABELS, fontsize=7)
        for i in range(grid.shape[0]):
            for j in range(grid.shape[1]):
                v = int(grid[i, j])
                if v == 0:
                    ax.text(j, i, "–", ha="center", va="center",
                            fontsize=7, color="gray")
                else:
                    color = "white" if v > grid.max() * 0.5 else "black"
                    ax.text(j, i, f"{v:,}", ha="center", va="center",
                            fontsize=6, color=color)
        ax.set_title(lbl, fontsize=8)
        ax.set_xlabel("Tramo Fan-Out", fontsize=8)
        ax.set_ylabel("Tramo Fan-In", fontsize=8)
    fig.suptitle("Grilla conjunta Fan-In × Fan-Out", fontsize=11)
    fig.text(0.5, 0.01,
             "Conteo de paquetes por combinación de tramos. Escala de color logarítmica.",
             ha="center", fontsize=7, style="italic")
    fig.tight_layout(rect=[0, 0.04, 1, 0.95])
    path = FIG_DIR / "fig01_joint_grid.png"
    fig.savefig(str(path), dpi=150)
    plt.close(fig)
    return str(path)

def fig02_retention_B_over_A(groups, families):
    _ensure_fig_dir()
    ret = families["retention"]["joint_grid"]
    grid_pct = np.full((len(FI_LABELS), len(FO_LABELS)), np.nan)
    grid_na = np.full((len(FI_LABELS), len(FO_LABELS)), 0)
    for row in ret:
        i = FI_LABELS.index(row["fi_tramo"])
        j = FO_LABELS.index(row["fo_tramo"])
        grid_pct[i, j] = row["pct"]
        grid_na[i, j] = row["n_a"]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    im = ax.imshow(grid_pct, aspect="auto", cmap="YlGn", vmin=0, vmax=100)
    ax.set_xticks(range(len(FO_LABELS)))
    ax.set_xticklabels(FO_LABELS, fontsize=7)
    ax.set_yticks(range(len(FI_LABELS)))
    ax.set_yticklabels(FI_LABELS, fontsize=7)
    for i in range(len(FI_LABELS)):
        for j in range(len(FO_LABELS)):
            na = grid_na[i, j]
            pct = grid_pct[i, j]
            if na == 0:
                ax.text(j, i, "–", ha="center", va="center",
                        fontsize=8, color="gray")
            else:
                color = "white" if pct > 65 else "black"
                ax.text(j, i, f"{pct:.1f}%", ha="center", va="center",
                        fontsize=8, color=color)
                ax.text(j, i + 0.35, f"N={na:,}", ha="center", va="center",
                        fontsize=5, color=color, alpha=0.7)
    ax.set_xlabel("Tramo Fan-Out", fontsize=8)
    ax.set_ylabel("Tramo Fan-In", fontsize=8)
    ax.set_title("Retención de A en B por celda de la grilla conjunta",
                 fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.8, label="% retenido")
    fig.text(0.5, 0.01,
             "Porcentaje de paquetes de A (con familias) que permanecen en B (sin familias).",
             ha="center", fontsize=7, style="italic")
    fig.tight_layout(rect=[0, 0.04, 1, 0.97])
    path = FIG_DIR / "fig02_retention_B_over_A.png"
    fig.savefig(str(path), dpi=150)
    plt.close(fig)
    return str(path)

def fig03_band_change(families):
    _ensure_fig_dir()
    sc = families["stratum_change"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, key, labels, title in [
        (axes[0], "xt_fi", FI_LABELS, "Fan-In"),
        (axes[1], "xt_fo", FO_LABELS, "Fan-Out"),
    ]:
        xt = sc[key].values.astype("float64")
        row_sums = xt.sum(axis=1, keepdims=True)
        pct = np.where(row_sums > 0, xt / row_sums * 100, 0.0)
        _draw_heatmap(ax, pct, labels, labels, fmt=".1f",
                      cmap="Blues", vmin=0, vmax=100, annot_size=7,
                      title=f"Cambio de tramo {title}: A → A externo",
                      xlabel=f"Tramo externo ({title})",
                      ylabel=f"Tramo total ({title})")
    fig.text(0.5, 0.01,
             "Porcentaje por fila. Cada fila muestra cómo se redistribuyen los paquetes al quitar vínculos internos.",
             ha="center", fontsize=7, style="italic")
    fig.tight_layout(rect=[0, 0.04, 1, 0.97])
    path = FIG_DIR / "fig03_band_change_A_to_A_external.png"
    fig.savefig(str(path), dpi=150)
    plt.close(fig)
    return str(path)

def _fig_rho_heatmap(measures, target, filename, title_target):
    _ensure_fig_dir()
    sp_key = f"sp_{target}"
    vars_list = list(measures[GROUP_LABELS[0]]["spearman"][sp_key].index)
    n_vars = len(vars_list)
    data = np.full((n_vars, 6), np.nan)
    for g_idx, lbl in enumerate(GROUP_LABELS):
        sp = measures[lbl]["spearman"][sp_key]
        for v_idx, v in enumerate(vars_list):
            data[v_idx, g_idx * 2] = sp.loc[v, "all"]
            col2 = f"{target}>0"
            data[v_idx, g_idx * 2 + 1] = sp.loc[v, col2]
    fig, ax = plt.subplots(figsize=(8, max(4, n_vars * 0.38)))
    _rho_heatmap(ax, data, vars_list, [])
    ax.set_xticks(range(6))
    # Two-level header
    for g_idx, short in enumerate(GROUP_SHORT):
        ax.text(g_idx * 2 + 0.5, -1.7, short, ha="center", va="center",
                fontsize=8, fontweight="bold",
                transform=ax.get_xaxis_transform())
    sub_labels = ["Todos", "Solo\npositivos"] * 3
    ax.set_xticklabels(sub_labels, fontsize=6)
    ax.set_title(f"ρ de Spearman con {title_target}", fontsize=10)
    note = (f"Correlación de Spearman de cada variable con {title_target}. "
            "fan_in_dev y fan_out_dev: valor total, sin descontar familias.")
    fig.text(0.5, 0.01, note, ha="center", fontsize=7, style="italic")
    fig.tight_layout(rect=[0, 0.04, 1, 0.97])
    path = FIG_DIR / filename
    fig.savefig(str(path), dpi=150)
    plt.close(fig)
    return str(path)
def fig04_rho_fan_in(measures):
    return _fig_rho_heatmap(measures, "fi", "fig04_rho_fan_in.png", "Fan-In")
def fig05_rho_fan_out(measures):
    return _fig_rho_heatmap(measures, "fo", "fig05_rho_fan_out.png", "Fan-Out")

def fig06_rho_by_group(measures):
    _ensure_fig_dir()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, target, title in [(axes[0], "fi", "Fan-In"),
                               (axes[1], "fo", "Fan-Out")]:
        sp_key = f"sp_{target}"
        vars_list = list(measures[GROUP_LABELS[0]]["spearman"][sp_key].index)
        x = np.arange(len(vars_list))
        w = 0.25
        for g_idx, lbl in enumerate(GROUP_LABELS):
            sp = measures[lbl]["spearman"][sp_key]
            vals = [sp.loc[v, "all"] for v in vars_list]
            ax.bar(x + g_idx * w, vals, w, label=GROUP_SHORT[g_idx])
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_xticks(x + w)
        ax.set_xticklabels(vars_list, rotation=45, ha="right", fontsize=7)
        ax.set_title(f"ρ de Spearman con {title} (todos los paquetes)",
                     fontsize=9)
        ax.set_ylabel("ρ", fontsize=9)
        ax.legend(fontsize=7)
    fig.text(0.5, 0.01,
             "ρ de Spearman de cada variable con Fan-In y Fan-Out. "
             "fan_in_dev y fan_out_dev: valor total, sin descontar familias.",
             ha="center", fontsize=7, style="italic")
    fig.tight_layout(rect=[0, 0.04, 1, 0.97])
    path = FIG_DIR / "fig06_rho_by_group.png"
    fig.savefig(str(path), dpi=150)
    plt.close(fig)
    return str(path)

def fig07_auc_and_nmi(measures):
    _ensure_fig_dir()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    targets = [("fi", "Fan-In"), ("fo", "Fan-Out")]
    # Top row: AUC
    for col, (t_name, t_title) in enumerate(targets):
        ax = axes[0, col]
        vars_list = VARS
        x = np.arange(len(vars_list))
        w = 0.25
        for g_idx, lbl in enumerate(GROUP_LABELS):
            auc_data = measures[lbl]["auc_mw"]
            vals = []
            for v in vars_list:
                match = [r for r in auc_data
                         if r["target"] == t_name and r["variable"] == v]
                vals.append(match[0]["auc"] if match else np.nan)
            ax.bar(x + g_idx * w, vals, w, label=GROUP_SHORT[g_idx])
        ax.axhline(0.5, color="red", linewidth=0.8, linestyle="--")
        ax.set_xticks(x + w)
        ax.set_xticklabels(vars_list, rotation=45, ha="right", fontsize=7)
        ax.set_title(f"AUC Mann-Whitney — {t_title}", fontsize=9)
        ax.set_ylabel("AUC", fontsize=9)
        ax.legend(fontsize=6)
    # Bottom row: NMI
    for col, (t_name, t_title) in enumerate(targets):
        ax = axes[1, col]
        x = np.arange(len(VARS))
        w = 0.25
        for g_idx, lbl in enumerate(GROUP_LABELS):
            nmi_data = measures[lbl]["nmi"]
            vals = []
            for v in VARS:
                match = [r for r in nmi_data
                         if r["target"] == t_name and r["variable"] == v]
                vals.append(match[0]["nmi"] if match else np.nan)
            ax.bar(x + g_idx * w, vals, w, label=GROUP_SHORT[g_idx])
        ax.set_xticks(x + w)
        ax.set_xticklabels(VARS, rotation=45, ha="right", fontsize=7)
        ax.set_title(f"Información mutua normalizada — {t_title}", fontsize=9)
        ax.set_ylabel("NMI", fontsize=9)
        ax.legend(fontsize=6)
    fig.text(0.5, 0.01,
             "AUC: capacidad de la variable para separar paquetes con/sin dependientes o dependencias. "
             "NMI: información compartida con el tramo. "
             "fan_in_dev y fan_out_dev: valor total, sin descontar familias.",
             ha="center", fontsize=7, style="italic")
    fig.tight_layout(rect=[0, 0.04, 1, 0.97])
    path = FIG_DIR / "fig07_auc_and_mutual_information.png"
    fig.savefig(str(path), dpi=150)
    plt.close(fig)
    return str(path)

def fig08_permutation_importance(measures):
    _ensure_fig_dir()
    targets = [("fi", "Fan-In"), ("fo", "Fan-Out")]
    any_model = any(measures[lbl]["model"] is not None for lbl in GROUP_LABELS)
    if not any_model:
        print("  fig08: no hay modelos, se omite")
        return None
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for row, (t_name, t_title) in enumerate(targets):
        for col, lbl in enumerate(GROUP_LABELS):
            ax = axes[row, col]
            model = measures[lbl]["model"]
            if model is None or t_name not in model:
                ax.text(0.5, 0.5, "Modelo no disponible", ha="center",
                        va="center", fontsize=9, transform=ax.transAxes)
                ax.set_title(f"{GROUP_SHORT[col]} — {t_title}", fontsize=8)
                continue
            imp = model[t_name]["imp_clf"]
            sorted_vars = sorted(imp.keys(), key=lambda k: imp[k])
            vals = [imp[v] for v in sorted_vars]
            y = np.arange(len(sorted_vars))
            ax.barh(y, vals, color="steelblue")
            ax.set_yticks(y)
            ax.set_yticklabels(sorted_vars, fontsize=7)
            ax.set_title(f"{GROUP_SHORT[col]} — {t_title}", fontsize=8)
            ax.set_xlabel("Importancia", fontsize=7)
    fig.suptitle("Importancia por permutación (clasificador)", fontsize=11)
    fig.text(0.5, 0.01,
             "Importancia por permutación del clasificador HistGBT (>0 vs =0). "
             "fan_in_dev y fan_out_dev: valor total, sin descontar familias.",
             ha="center", fontsize=7, style="italic")
    fig.tight_layout(rect=[0, 0.04, 1, 0.95])
    path = FIG_DIR / "fig08_permutation_importance.png"
    fig.savefig(str(path), dpi=150)
    plt.close(fig)
    return str(path)

def fig09_model_ceiling(measures):
    _ensure_fig_dir()
    any_model = any(measures[lbl]["model"] is not None for lbl in GROUP_LABELS)
    if not any_model:
        print("  fig09: no hay modelos, se omite")
        return None
    targets = [("fi", "Fan-In"), ("fo", "Fan-Out")]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    # Panel 1: R2
    ax = axes[0]
    x = np.arange(len(targets))
    w = 0.25
    for g_idx, lbl in enumerate(GROUP_LABELS):
        model = measures[lbl]["model"]
        vals = []
        for t_name, _ in targets:
            if model is None or t_name not in model:
                vals.append(0)
            else:
                vals.append(model[t_name]["r2"])
        ax.bar(x + g_idx * w, vals, w, label=GROUP_SHORT[g_idx])
    ax.set_xticks(x + w)
    ax.set_xticklabels([t[1] for t in targets], fontsize=8)
    ax.set_title("R² del regresor (log1p)", fontsize=9)
    ax.set_ylabel("R²", fontsize=9)
    ax.legend(fontsize=7)
    # Panel 2: AUC
    ax = axes[1]
    for g_idx, lbl in enumerate(GROUP_LABELS):
        model = measures[lbl]["model"]
        vals = []
        for t_name, _ in targets:
            if model is None or t_name not in model:
                vals.append(0.5)
            else:
                vals.append(model[t_name]["auc"])
        ax.bar(x + g_idx * w, vals, w, label=GROUP_SHORT[g_idx])
    ax.axhline(0.5, color="red", linewidth=0.8, linestyle="--")
    ax.set_xticks(x + w)
    ax.set_xticklabels([t[1] for t in targets], fontsize=8)
    ax.set_title("AUC del clasificador (>0 vs =0)", fontsize=9)
    ax.set_ylabel("AUC", fontsize=9)
    ax.legend(fontsize=7)
    fig.suptitle("Techo de explicación del modelo HistGBT", fontsize=11)
    fig.text(0.5, 0.01,
             "R² sobre log1p del objetivo y AUC para clasificación binaria. "
             "fan_in_dev y fan_out_dev: valor total, sin descontar familias.",
             ha="center", fontsize=7, style="italic")
    fig.tight_layout(rect=[0, 0.04, 1, 0.93])
    path = FIG_DIR / "fig09_model_ceiling.png"
    fig.savefig(str(path), dpi=150)
    plt.close(fig)
    return str(path)

_PROFILE_PANELS = [
    ("med_n_versions", "Mediana n_versions"),
    ("med_n_maintainers", "Mediana n_maintainers"),
    ("med_n_keywords", "Mediana n_keywords"),
    ("med_age_years", "Mediana age_years"),
    ("pct_has_github", "% con GitHub"),
    ("pct_scoped", "% con scope"),
]
def _fig_profile_by_band(groups, profile_key, labels, xlabel, filename):
    _ensure_fig_dir()
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes_flat = axes.flatten()
    for p_idx, (col, ylabel) in enumerate(_PROFILE_PANELS):
        ax = axes_flat[p_idx]
        for g_idx, lbl in enumerate(GROUP_LABELS):
            profile = groups[lbl][profile_key]
            x_vals = []
            y_vals = []
            for row in profile:
                if col in row:
                    x_vals.append(row["level"])
                    y_vals.append(row[col])
            ax.plot(range(len(x_vals)), y_vals, marker="o", markersize=4,
                    label=GROUP_SHORT[g_idx], linewidth=1.5)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, fontsize=7)
        ax.set_title(ylabel, fontsize=9)
        ax.set_xlabel(xlabel, fontsize=7)
        ax.legend(fontsize=6)
    fig.text(0.5, 0.01,
             f"Perfil de variables por {xlabel.lower()}. "
             "fan_in_dev y fan_out_dev: valor total, sin descontar familias.",
             ha="center", fontsize=7, style="italic")
    fig.tight_layout(rect=[0, 0.04, 1, 0.97])
    path = FIG_DIR / filename
    fig.savefig(str(path), dpi=150)
    plt.close(fig)
    return str(path)
def fig10_profile_by_fi_band(groups):
    return _fig_profile_by_band(groups, "profile_fi", FI_LABELS,
                                "Tramo Fan-In",
                                "fig10_profile_by_fan_in_band.png")
def fig11_profile_by_fo_band(groups):
    return _fig_profile_by_band(groups, "profile_fo", FO_LABELS,
                                "Tramo Fan-Out",
                                "fig11_profile_by_fan_out_band.png")

def fig12_profile_by_zero_cell(groups):
    _ensure_fig_dir()
    short_names = ["Aislado", "Consumidor", "Consumido\nsin consumir",
                   "Con ambas\nconexiones"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes_flat = axes.flatten()
    for p_idx, (col, ylabel) in enumerate(_PROFILE_PANELS):
        ax = axes_flat[p_idx]
        x = np.arange(len(ZERO_NAMES))
        w = 0.25
        for g_idx, lbl in enumerate(GROUP_LABELS):
            profile = groups[lbl]["profile_zeros"]
            vals = []
            for row in profile:
                vals.append(row.get(col, 0))
            ax.bar(x + g_idx * w, vals, w, label=GROUP_SHORT[g_idx])
        ax.set_xticks(x + w)
        ax.set_xticklabels(short_names, fontsize=7)
        ax.set_title(ylabel, fontsize=9)
        ax.legend(fontsize=6)
    fig.text(0.5, 0.01,
             "Perfil de variables por celda de ceros. "
             "fan_in_dev y fan_out_dev: valor total, sin descontar familias.",
             ha="center", fontsize=7, style="italic")
    fig.tight_layout(rect=[0, 0.04, 1, 0.97])
    path = FIG_DIR / "fig12_profile_by_zero_cell.png"
    fig.savefig(str(path), dpi=150)
    plt.close(fig)
    return str(path)

def fig13_internal_vs_external(families):
    _ensure_fig_dir()
    ie = families["internal_external"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, key, labels, title in [
        (axes[0], "fan_in", FI_LABELS, "Fan-In"),
        (axes[1], "fan_out", FO_LABELS, "Fan-Out"),
    ]:
        rows = [r for r in ie[key] if r["tramo"] != "Total"]
        pct_int = [r["pct_internal"] for r in rows]
        pct_ext = [100 - r["pct_internal"] for r in rows]
        x = np.arange(len(labels))
        ax.bar(x, pct_int, label="Interno", color="steelblue")
        ax.bar(x, pct_ext, bottom=pct_int, label="Externo", color="coral")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_ylabel("% del total", fontsize=8)
        ax.set_xlabel(f"Tramo {title}", fontsize=8)
        ax.set_title(f"Composición interna/externa — {title}", fontsize=9)
        ax.legend(fontsize=7)
        ax.set_ylim(0, 100)
    fig.suptitle("Porcentaje interno vs. externo por tramo (grupo A)",
                 fontsize=11)
    fig.text(0.5, 0.01,
             "Barras apiladas al 100%. Solo población A (con familias).",
             ha="center", fontsize=7, style="italic")
    fig.tight_layout(rect=[0, 0.04, 1, 0.93])
    path = FIG_DIR / "fig13_internal_vs_external_A.png"
    fig.savefig(str(path), dpi=150)
    plt.close(fig)
    return str(path)

def generate_figures(groups, families, measures):
    print("\nGenerating figures ...")
    paths = {}
    paths["fig01"] = fig01_joint_grid(groups)
    paths["fig02"] = fig02_retention_B_over_A(groups, families)
    paths["fig03"] = fig03_band_change(families)
    paths["fig04"] = fig04_rho_fan_in(measures)
    paths["fig05"] = fig05_rho_fan_out(measures)
    paths["fig06"] = fig06_rho_by_group(measures)
    paths["fig07"] = fig07_auc_and_nmi(measures)
    paths["fig08"] = fig08_permutation_importance(measures)
    paths["fig09"] = fig09_model_ceiling(measures)
    paths["fig10"] = fig10_profile_by_fi_band(groups)
    paths["fig11"] = fig11_profile_by_fo_band(groups)
    paths["fig12"] = fig12_profile_by_zero_cell(groups)
    paths["fig13"] = fig13_internal_vs_external(families)
    written = {k: v for k, v in paths.items() if v is not None}
    print(f"  {len(written)} figures written")
    return paths

# ── Step 4: markdown report ──────────────────────────────────────────
REPORT_DIR = ROOT / "data" / "08b_variable_selection"
REPORT_PATH = REPORT_DIR / "variable_selection_results.md"
SIGN_DIFF_MIN = 0.03
def _fmt_int(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    return f"{int(v):,}".replace(",", ".")
def _fmt_pct(v, decimals=1):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    fmt = f"{{:.{decimals}f}}"
    return fmt.format(v).replace(".", ",")
def _fmt_rho(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    return f"{v:.3f}".replace(".", ",")
def _md_table(headers, rows, align=None):
    if align is None:
        align = ["l"] + ["r"] * (len(headers) - 1)
    sep = []
    for a in align:
        if a == "r":
            sep.append("---:")
        elif a == "c":
            sep.append(":---:")
        else:
            sep.append(":---")
    lines = ["| " + " | ".join(str(h) for h in headers) + " |",
             "| " + " | ".join(sep) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)
def _get_sp_all(meas, target, var):
    return meas["spearman"][f"sp_{target}"].loc[var, "all"]
def _get_model_val(meas, target, key):
    m = meas["model"]
    if m is None or target not in m:
        return None
    return m[target][key]
def build_comparison_table(groups, measures, families):
    lbl_a, lbl_ae, lbl_b = GROUP_LABELS
    ga, gae, gb = groups[lbl_a], groups[lbl_ae], groups[lbl_b]
    ma, mae, mb = measures[lbl_a], measures[lbl_ae], measures[lbl_b]
    def _z(g, name):
        for z in g["zeros"]:
            if z["cell"] == name:
                return z["pct"]
        return 0
    def _vs(g, var, key):
        for s in g["var_stats"]:
            if s["variable"] == var:
                return s.get(key, None)
        return None
    ie = families["internal_external"]
    ie_fi_total = ie["fan_in"][-1]
    ie_fo_total = ie["fan_out"][-1]
    ret = families["retention"]
    total_a = sum(r["n_a"] for r in ret["fi_tramo"])
    total_ret = sum(r["n_retained"] for r in ret["fi_tramo"])
    pct_ret = total_ret / total_a * 100 if total_a > 0 else 0
    rows = []
    rows.append(("N", _fmt_int(ga["n"]), _fmt_int(gae["n"]), _fmt_int(gb["n"])))
    rows.append(("% Fan-In = 0", _fmt_pct(_z(ga, ZERO_NAMES[0]) + _z(ga, ZERO_NAMES[1])),
                 _fmt_pct(_z(gae, ZERO_NAMES[0]) + _z(gae, ZERO_NAMES[1])),
                 _fmt_pct(_z(gb, ZERO_NAMES[0]) + _z(gb, ZERO_NAMES[1]))))
    rows.append(("% Fan-Out = 0", _fmt_pct(_z(ga, ZERO_NAMES[0]) + _z(ga, ZERO_NAMES[2])),
                 _fmt_pct(_z(gae, ZERO_NAMES[0]) + _z(gae, ZERO_NAMES[2])),
                 _fmt_pct(_z(gb, ZERO_NAMES[0]) + _z(gb, ZERO_NAMES[2]))))
    rows.append(("% Aislados", _fmt_pct(_z(ga, ZERO_NAMES[0])),
                 _fmt_pct(_z(gae, ZERO_NAMES[0])),
                 _fmt_pct(_z(gb, ZERO_NAMES[0]))))
    rows.append(("p99 Fan-In", _fmt_int(_vs(ga, "fi", "p99")),
                 _fmt_int(_vs(gae, "fi", "p99")),
                 _fmt_int(_vs(gb, "fi", "p99"))))
    rows.append(("p99 Fan-Out", _fmt_int(_vs(ga, "fo", "p99")),
                 _fmt_int(_vs(gae, "fo", "p99")),
                 _fmt_int(_vs(gb, "fo", "p99"))))
    rows.append(("ρ Fan-In ↔ Fan-Out", _fmt_rho(ma["fi_fo_rho"]["all"]),
                 _fmt_rho(mae["fi_fo_rho"]["all"]),
                 _fmt_rho(mb["fi_fo_rho"]["all"])))
    for v in VARS:
        rows.append((f"ρ {v} – Fan-In",
                     _fmt_rho(_get_sp_all(ma, "fi", v)),
                     _fmt_rho(_get_sp_all(mae, "fi", v)),
                     _fmt_rho(_get_sp_all(mb, "fi", v))))
        rows.append((f"ρ {v} – Fan-Out",
                     _fmt_rho(_get_sp_all(ma, "fo", v)),
                     _fmt_rho(_get_sp_all(mae, "fo", v)),
                     _fmt_rho(_get_sp_all(mb, "fo", v))))
    for t in ("fi", "fo"):
        t_label = "Fan-In" if t == "fi" else "Fan-Out"
        r2 = _get_model_val(ma, t, "r2")
        rows.append((f"R² {t_label}",
                     _fmt_rho(r2) if r2 is not None else "–",
                     _fmt_rho(_get_model_val(mae, t, "r2")) if _get_model_val(mae, t, "r2") is not None else "–",
                     _fmt_rho(_get_model_val(mb, t, "r2")) if _get_model_val(mb, t, "r2") is not None else "–"))
        auc = _get_model_val(ma, t, "auc")
        rows.append((f"AUC {t_label}",
                     _fmt_rho(auc) if auc is not None else "–",
                     _fmt_rho(_get_model_val(mae, t, "auc")) if _get_model_val(mae, t, "auc") is not None else "–",
                     _fmt_rho(_get_model_val(mb, t, "auc")) if _get_model_val(mb, t, "auc") is not None else "–"))
        rows.append((f"Variable top {t_label}",
                     _get_model_val(ma, t, "top_clf") or "–",
                     _get_model_val(mae, t, "top_clf") or "–",
                     _get_model_val(mb, t, "top_clf") or "–"))
    rows.append(("% interno Fan-In", _fmt_pct(ie_fi_total["pct_internal"]), "–", "–"))
    rows.append(("% interno Fan-Out", _fmt_pct(ie_fo_total["pct_internal"]), "–", "–"))
    rows.append(("Retención B/A", "–", "–", _fmt_pct(pct_ret)))
    return _md_table(["Métrica", "A", "A externo", "B"], rows)
def _grid_md(grid_df, title):
    headers = ["FI \\ FO"] + list(grid_df.columns)
    rows = []
    for idx in grid_df.index:
        row = [str(idx)]
        for col in grid_df.columns:
            row.append(_fmt_int(grid_df.loc[idx, col]))
        rows.append(row)
    return f"**{title}**\n\n" + _md_table(headers, rows)
def _spearman_side_by_side(measures, target):
    sp_key = f"sp_{target}"
    t_label = "Fan-In" if target == "fi" else "Fan-Out"
    pos_label = f"{target}>0"
    vars_list = list(measures[GROUP_LABELS[0]]["spearman"][sp_key].index)
    headers = ["Variable"]
    for short in GROUP_SHORT:
        headers += [f"{short} Todos", f"{short} Positivos"]
    rows = []
    for v in vars_list:
        row = [v]
        for lbl in GROUP_LABELS:
            sp = measures[lbl]["spearman"][sp_key]
            row.append(_fmt_rho(sp.loc[v, "all"]))
            row.append(_fmt_rho(sp.loc[v, pos_label]))
        rows.append(row)
    return f"**ρ de Spearman con {t_label}**\n\n" + _md_table(
        headers, rows, ["l"] + ["r"] * (len(headers) - 1))
def _spearman_diff_table(measures, target):
    sp_key = f"sp_{target}"
    t_label = "Fan-In" if target == "fi" else "Fan-Out"
    lbl_a, lbl_ae, lbl_b = GROUP_LABELS
    vars_list = list(measures[lbl_a]["spearman"][sp_key].index)
    headers = ["Variable", "A ext − A", "", "B − A ext", ""]
    rows = []
    for v in vars_list:
        ra = measures[lbl_a]["spearman"][sp_key].loc[v, "all"]
        rae = measures[lbl_ae]["spearman"][sp_key].loc[v, "all"]
        rb = measures[lbl_b]["spearman"][sp_key].loc[v, "all"]
        d1 = rae - ra
        d2 = rb - rae
        mark1 = " ⚠" if abs(d1) >= SIGN_DIFF_MIN and np.sign(ra) != np.sign(rae) and ra != 0 and rae != 0 else ""
        mark2 = " ⚠" if abs(d2) >= SIGN_DIFF_MIN and np.sign(rae) != np.sign(rb) and rae != 0 and rb != 0 else ""
        rows.append([v, _fmt_rho(d1), mark1, _fmt_rho(d2), mark2])
    return f"**Diferencias de ρ con {t_label} (todos)**\n\n" + _md_table(
        headers, rows, ["l", "r", "c", "r", "c"])
def write_md(groups, families, measures, fig_paths):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["# Resultados: selección de variables (08b)\n"]
    # Section 1
    lines.append("## 1. Los tres grupos\n")
    lines.append("| Grupo | Etiqueta | Fan-In | Fan-Out |")
    lines.append("|:---|:---|:---|:---|")
    lines.append("| A | A: con familias | fan_in | fan_out |")
    lines.append("| A externo | A externo: mismos paquetes, solo vínculos externos | fan_in_external | fan_out_external |")
    lines.append("| B | B: sin familias | fan_in | fan_out |")
    lines.append("")
    lines.append("fan_in_dev y fan_out_dev se usan con su valor total, sin descontar familias, en los tres grupos.\n")
    # Section 2
    lines.append("## 2. Tabla comparativa\n")
    lines.append(build_comparison_table(groups, measures, families))
    lines.append("")
    # Section 3
    lines.append("## 3. Tamaño y ceros\n")
    for lbl in GROUP_LABELS:
        g = groups[lbl]
        headers = ["Celda", "N", "%"]
        rows = [(z["cell"], _fmt_int(z["n"]), _fmt_pct(z["pct"])) for z in g["zeros"]]
        lines.append(f"**{lbl}** (N = {_fmt_int(g['n'])})\n")
        lines.append(_md_table(headers, rows))
        lines.append("")
    # Section 4
    lines.append("## 4. Grilla conjunta\n")
    for lbl in GROUP_LABELS:
        lines.append(_grid_md(groups[lbl]["joint_grid"], lbl))
        lines.append("")
    # Section 5
    lines.append("## 5. Estadísticos por variable\n")
    for lbl in GROUP_LABELS:
        g = groups[lbl]
        headers = ["Variable", "% cero", "Mediana", "p90", "p99", "Máx"]
        rows_n = []
        rows_b = []
        for s in g["var_stats"]:
            if "pct_true" in s:
                rows_b.append((s["variable"], _fmt_pct(s["pct_true"])))
            else:
                rows_n.append((s["variable"], _fmt_pct(s["pct_zero"]),
                              _fmt_rho(s["median"]), _fmt_int(s.get("p90")),
                              _fmt_int(s.get("p99")), _fmt_int(s.get("max"))))
        lines.append(f"**{lbl}**\n")
        lines.append(_md_table(headers, rows_n))
        lines.append("")
        if rows_b:
            lines.append(_md_table(["Variable", "% verdadero"], rows_b))
            lines.append("")
    # Section 6
    lines.append("## 6. Spearman\n")
    for target in ("fi", "fo"):
        lines.append(_spearman_side_by_side(measures, target))
        lines.append("")
        lines.append(_spearman_diff_table(measures, target))
        lines.append("")
    # Section 7
    lines.append("## 7. Correlación entre Fan-In y Fan-Out y pares redundantes\n")
    headers = ["Grupo", "ρ todos", "ρ ambos > 0"]
    rows = []
    for lbl in GROUP_LABELS:
        fifo = measures[lbl]["fi_fo_rho"]
        rows.append((lbl, _fmt_rho(fifo["all"]), _fmt_rho(fifo["both_gt0"])))
    lines.append(_md_table(headers, rows))
    lines.append("")
    for lbl in GROUP_LABELS:
        rp = measures[lbl]["redundant_pairs"]
        if rp:
            lines.append(f"**Pares redundantes (|ρ| > {_fmt_rho(REDUNDANCY_THRESHOLD)}) — {lbl}**\n")
            headers_r = ["Variable 1", "Variable 2", "ρ"]
            rows_r = [(a, b, _fmt_rho(r)) for a, b, r in rp]
            lines.append(_md_table(headers_r, rows_r))
            lines.append("")
        else:
            lines.append(f"Sin pares redundantes — {lbl}\n")
    # Section 8
    lines.append("## 8. AUC Mann-Whitney\n")
    for target, t_label in [("fi", "Fan-In"), ("fo", "Fan-Out")]:
        headers = ["Variable"] + [s for s in GROUP_SHORT]
        rows = []
        for v in VARS:
            row = [v]
            for lbl in GROUP_LABELS:
                match = [r for r in measures[lbl]["auc_mw"]
                         if r["target"] == target and r["variable"] == v]
                row.append(_fmt_rho(match[0]["auc"]) if match else "–")
            rows.append(row)
        lines.append(f"**AUC con {t_label}**\n")
        lines.append(_md_table(headers, rows))
        lines.append("")
    # Section 9
    lines.append("## 9. Tamaño de efecto\n")
    for target, t_label in [("fi", "Fan-In"), ("fo", "Fan-Out")]:
        headers = ["Variable", "Medida"] + list(GROUP_SHORT)
        rows = []
        for v in VARS:
            row = [v]
            measure_name = "Cramér V" if v in BINARY_VARS else "ε²"
            row.append(measure_name)
            for lbl in GROUP_LABELS:
                match = [r for r in measures[lbl]["effect_sizes"]
                         if r["target"] == target and r["variable"] == v]
                row.append(_fmt_rho(match[0]["value"]) if match else "–")
            rows.append(row)
        lines.append(f"**Efecto con {t_label}**\n")
        lines.append(_md_table(headers, rows))
        lines.append("")
    # Section 10
    lines.append("## 10. Información mutua normalizada\n")
    for target, t_label in [("fi", "Fan-In"), ("fo", "Fan-Out")]:
        headers = ["Variable"] + list(GROUP_SHORT)
        rows = []
        for v in VARS:
            row = [v]
            for lbl in GROUP_LABELS:
                match = [r for r in measures[lbl]["nmi"]
                         if r["target"] == target and r["variable"] == v]
                row.append(_fmt_rho(match[0]["nmi"]) if match else "–")
            rows.append(row)
        lines.append(f"**NMI con {t_label}**\n")
        lines.append(_md_table(headers, rows))
        lines.append("")
    # Section 11
    lines.append("## 11. Techo de explicación e importancia por permutación\n")
    any_model = any(measures[lbl]["model"] is not None for lbl in GROUP_LABELS)
    if not any_model:
        lines.append("Modelo no disponible (scikit-learn no instalado).\n")
    else:
        headers = ["Grupo", "Objetivo", "R²", "AUC", "Top regresor", "Top clasificador"]
        rows = []
        for lbl, short in zip(GROUP_LABELS, GROUP_SHORT):
            m = measures[lbl]["model"]
            for t, t_label in [("fi", "Fan-In"), ("fo", "Fan-Out")]:
                if m is None or t not in m:
                    rows.append((short, t_label, "–", "–", "–", "–"))
                else:
                    rows.append((short, t_label, _fmt_rho(m[t]["r2"]),
                                _fmt_rho(m[t]["auc"]),
                                m[t]["top_reg"], m[t]["top_clf"]))
        lines.append(_md_table(headers, rows))
        lines.append("")
        for lbl, short in zip(GROUP_LABELS, GROUP_SHORT):
            m = measures[lbl]["model"]
            if m is None:
                continue
            for t, t_label in [("fi", "Fan-In"), ("fo", "Fan-Out")]:
                if t not in m:
                    continue
                imp = m[t]["imp_clf"]
                sorted_v = sorted(imp.keys(), key=lambda k: imp[k], reverse=True)
                headers_i = ["Variable", "Importancia"]
                rows_i = [(v, _fmt_rho(imp[v])) for v in sorted_v]
                lines.append(f"**Importancia clasificador — {short} — {t_label}**\n")
                lines.append(_md_table(headers_i, rows_i))
                lines.append("")
    # Section 12
    lines.append("## 12. Perfiles por tramo y celda de ceros\n")
    for profile_key, p_labels, p_title in [
        ("profile_fi", FI_LABELS, "tramo de Fan-In"),
        ("profile_fo", FO_LABELS, "tramo de Fan-Out"),
        ("profile_zeros", ZERO_NAMES, "celda de ceros"),
    ]:
        headers = ["Nivel", "Grupo", "N", "%"]
        for c in PROFILE_MED_COLS:
            headers.append(f"med_{c}")
        for c in PROFILE_PCT_COLS:
            headers.append(f"% {c}")
        for c in PROFILE_GT0_COLS:
            headers.append(f"% {c}>0")
        rows = []
        for level in p_labels:
            for lbl, short in zip(GROUP_LABELS, GROUP_SHORT):
                profile = groups[lbl][profile_key]
                row_data = [r for r in profile if r["level"] == level]
                if not row_data:
                    continue
                r = row_data[0]
                row = [level, short, _fmt_int(r["n"]), _fmt_pct(r["pct"])]
                for c in PROFILE_MED_COLS:
                    row.append(_fmt_rho(r.get(f"med_{c}", 0)))
                for c in PROFILE_PCT_COLS:
                    row.append(_fmt_pct(r.get(f"pct_{c}", 0)))
                for c in PROFILE_GT0_COLS:
                    row.append(_fmt_pct(r.get(f"pct_{c}_gt0", 0)))
                rows.append(row)
        lines.append(f"**Perfil por {p_title}**\n")
        lines.append(_md_table(headers, rows))
        lines.append("")
    # Section 13
    lines.append("## 13. Familias\n")
    ie = families["internal_external"]
    for key, title in [("fan_in", "Fan-In"), ("fan_out", "Fan-Out")]:
        headers = ["Tramo", "Interno", "Externo", "% interno"]
        rows = []
        for r in ie[key]:
            rows.append((r["tramo"], _fmt_int(r["sum_internal"]),
                        _fmt_int(r["sum_external"]),
                        _fmt_pct(r["pct_internal"])))
        lines.append(f"**Parte interna y externa — {title}**\n")
        lines.append(_md_table(headers, rows))
        lines.append("")
    sc = families["stratum_change"]
    lines.append("**Cambio de estrato A → A externo**\n")
    headers_sc = ["Cambio", "N", "%"]
    rows_sc = [(s["change"], _fmt_int(s["n"]), _fmt_pct(s["pct"]))
               for s in sc["summary"]]
    lines.append(_md_table(headers_sc, rows_sc))
    lines.append("")
    for key, title, labels in [
        ("xt_fi", "Fan-In", FI_LABELS),
        ("xt_fo", "Fan-Out", FO_LABELS),
        ("xt_zero", "Celda de ceros", ZERO_NAMES),
    ]:
        lines.append(_grid_md(sc[key], f"Cruce {title}: total vs externo"))
        lines.append("")
    ret = families["retention"]
    lines.append("**Retención B/A por grilla conjunta**\n")
    headers_r = ["FI tramo", "FO tramo", "N en A", "Retenidos", "%"]
    rows_r = [(r["fi_tramo"], r["fo_tramo"], _fmt_int(r["n_a"]),
              _fmt_int(r["n_retained"]), _fmt_pct(r["pct"]))
             for r in ret["joint_grid"]]
    lines.append(_md_table(headers_r, rows_r))
    lines.append("")
    for key, title in [("fi_tramo", "tramo Fan-In"), ("fo_tramo", "tramo Fan-Out"),
                       ("zero_cell", "celda de ceros"), ("creation_year", "año de creación"),
                       ("scoped", "scoped")]:
        headers_d = ["Nivel", "N en A", "Retenidos", "%"]
        rows_d = [(str(r["level"]), _fmt_int(r["n_a"]),
                  _fmt_int(r["n_retained"]), _fmt_pct(r["pct"]))
                 for r in ret[key]]
        lines.append(f"**Retención por {title}**\n")
        lines.append(_md_table(headers_d, rows_d))
        lines.append("")
    ls = families["leavers_stayers"]
    lines.append("**Los que salen vs los que se quedan**\n")
    ls_keys = [k for k in ls["stayers"].keys() if k != "n"]
    headers_ls = ["Métrica", "Salen (familia)", "Se quedan"]
    rows_ls = [("N", _fmt_int(ls["leavers"]["n"]), _fmt_int(ls["stayers"]["n"]))]
    for k in ls_keys:
        lv = ls["leavers"].get(k)
        sv = ls["stayers"].get(k)
        if isinstance(lv, dict):
            for sk, sv2 in lv.items():
                rows_ls.append((f"{k}: {sk}",
                               _fmt_pct(sv2) if isinstance(sv2, (int, float)) else str(sv2),
                               _fmt_pct(ls["stayers"][k].get(sk, 0)) if isinstance(ls["stayers"].get(k), dict) else "–"))
        elif isinstance(lv, (int, float)):
            if "pct" in k or "med" in k:
                rows_ls.append((k, _fmt_pct(lv), _fmt_pct(sv)))
            else:
                rows_ls.append((k, _fmt_rho(lv), _fmt_rho(sv)))
        else:
            rows_ls.append((k, str(lv), str(sv)))
    lines.append(_md_table(headers_ls, rows_ls))
    lines.append("")
    lines.append(f"*Nota: {ls['note_scoped_leavers']}*\n")
    # Section 14
    lines.append("## 14. Gráficos\n")
    fig_names = [
        ("fig01", "Grilla conjunta Fan-In × Fan-Out"),
        ("fig02", "Retención B/A por celda de la grilla"),
        ("fig03", "Cambio de tramo A → A externo"),
        ("fig04", "ρ de Spearman con Fan-In"),
        ("fig05", "ρ de Spearman con Fan-Out"),
        ("fig06", "ρ por grupo"),
        ("fig07", "AUC e información mutua"),
        ("fig08", "Importancia por permutación"),
        ("fig09", "Techo de explicación"),
        ("fig10", "Perfil por tramo Fan-In"),
        ("fig11", "Perfil por tramo Fan-Out"),
        ("fig12", "Perfil por celda de ceros"),
        ("fig13", "Interno vs externo (A)"),
    ]
    for key, caption in fig_names:
        p = fig_paths.get(key)
        if p is not None:
            fname = Path(p).name
            lines.append(f"**{caption}**\n")
            lines.append(f"![{caption}](figures/{fname})\n")
    md_text = "\n".join(lines)
    REPORT_PATH.write_text(md_text, encoding="utf-8")
    print(f"  md written: {REPORT_PATH}")
    return str(REPORT_PATH)

# ── Main ─────────────────────────────────────────────────────────────
def main():
    print("08b_variable_selection.py")
    # ── Population A ──
    print("\nLoading population A ...")
    df_a = load_parquet(PARQUET_A)
    print(f"  {len(df_a):,} packages")
    print("  Group: A ...")
    res_a = analyze_group(df_a, "fan_in", "fan_out", GROUP_DEFS[0][0])
    print("  Group: A externo ...")
    res_a_ext = analyze_group(
        df_a, "fan_in_external", "fan_out_external", GROUP_DEFS[1][0])
    print("  Measures: A ...")
    meas_a = analyze_measures(df_a, "fan_in", "fan_out",
                              GROUP_DEFS[0][0], PARQUET_A)
    print("  Measures: A externo ...")
    meas_a_ext = analyze_measures(df_a, "fan_in_external", "fan_out_external",
                                  GROUP_DEFS[1][0], PARQUET_A)
    print("  Family analysis ...")
    families = analyze_families(df_a)
    del df_a
    gc.collect()
    # ── Population B ──
    print("\nLoading population B ...")
    df_b = load_parquet(PARQUET_B)
    print(f"  {len(df_b):,} packages")
    print("  Group: B ...")
    res_b = analyze_group(df_b, "fan_in", "fan_out", GROUP_DEFS[2][0])
    print("  Measures: B ...")
    meas_b = analyze_measures(df_b, "fan_in", "fan_out",
                              GROUP_DEFS[2][0], PARQUET_B)
    del df_b
    gc.collect()
    # ── Assemble results ──
    all_groups = {
        GROUP_DEFS[0][0]: res_a,
        GROUP_DEFS[1][0]: res_a_ext,
        GROUP_DEFS[2][0]: res_b,
    }
    all_measures = {
        GROUP_DEFS[0][0]: meas_a,
        GROUP_DEFS[1][0]: meas_a_ext,
        GROUP_DEFS[2][0]: meas_b,
    }
    # ── Figures ──
    fig_paths = generate_figures(all_groups, families, all_measures)
    # ── Markdown ──
    print("\nWriting md ...")
    write_md(all_groups, families, all_measures, fig_paths)
    # ── Summary ──
    print("\n--- Resumen ---")
    sp_fi_var = "n_versions"
    headers = ["Grupo", "N", f"ρ({sp_fi_var}, fi)", f"ρ({sp_fi_var}, fo)"]
    for lbl, short in zip(GROUP_LABELS, GROUP_SHORT):
        n = all_groups[lbl]["n"]
        r_fi = _get_sp_all(all_measures[lbl], "fi", sp_fi_var)
        r_fo = _get_sp_all(all_measures[lbl], "fo", sp_fi_var)
        print(f"  {short:8s}  N={n:>12,}  ρ(n_versions,fi)={r_fi:+.3f}  ρ(n_versions,fo)={r_fo:+.3f}")
    print("\nDone.")
if __name__ == "__main__":
    main()
