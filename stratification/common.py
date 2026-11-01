# stratification/common.py -- shared loader, constants and metrics.
# Importable without side effects.
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "07_inclusion_packages"
PARQUET_B = DATA_DIR / "population_without_families.parquet"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

# ── Constants ────────────────────────────────────────────────────────
SEED = 42
SAMPLE_SIZE_EXAMPLE = 2000
MIN_STRATUM_REPORT = 500
SNAPSHOT_DATE = date(2026, 9, 18)
PARQUET_COLS = [
    "fan_in", "fan_out", "fan_in_dev", "fan_out_dev",
    "n_versions", "n_maintainers", "n_keywords", "n_peer", "n_opt",
    "created_date", "has_github", "deprecated", "scope",
]
VARS = [
    "n_versions", "n_maintainers", "n_keywords", "n_peer", "n_opt",
    "age_years", "has_github", "deprecated", "scoped",
    "fan_in_dev", "fan_out_dev",
]
ZERO_CELLS = [
    (0, "Aislado (Fan-In 0, Fan-Out 0)"),
    (1, "Consumidor (Fan-In 0, Fan-Out mayor a 0)"),
    (2, "Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0)"),
    (3, "Con ambas conexiones"),
]
ZERO_CELL_NAMES = [name for _, name in ZERO_CELLS]

# ── Dataset B loader ─────────────────────────────────────────────────
def load_dataset_b():
    df = pd.read_parquet(str(PARQUET_B), columns=PARQUET_COLS)
    # compact integer columns
    for col in ("fan_in", "fan_out", "fan_in_dev", "fan_out_dev",
                "n_versions", "n_maintainers", "n_keywords",
                "n_peer", "n_opt"):
        df[col] = df[col].fillna(0).astype("int32")
    # age in years
    days = (pd.Timestamp(SNAPSHOT_DATE)
            - pd.to_datetime(df["created_date"])).dt.days
    df["age_years"] = (days / 365.25).astype("float32")
    df.drop(columns=["created_date"], inplace=True)
    # binary flags as int8
    df["scoped"] = (df["scope"].fillna("").astype(str) != "").astype("int8")
    df.drop(columns=["scope"], inplace=True)
    for col in ("has_github", "deprecated"):
        df[col] = df[col].fillna(0).astype(bool).astype("int8")
    # short aliases
    df.rename(columns={"fan_in": "fi", "fan_out": "fo"}, inplace=True)
    # zero-cell code
    fi0 = df["fi"].values == 0
    fo0 = df["fo"].values == 0
    code = np.where(fi0 & fo0, 0,
           np.where(fi0 & ~fo0, 1,
           np.where(~fi0 & fo0, 2, 3))).astype(np.int8)
    df["zero_cell"] = code
    return df

# ── R² (eta-squared) by stratum ─────────────────────────────────────
def _r2_by_strata(values, labels, k):
    sums = np.bincount(labels, weights=values, minlength=k)
    counts = np.bincount(labels, minlength=k).astype(np.float64)
    mask = counts > 0
    grand_mean = values.mean()
    ss_total = ((values - grand_mean) ** 2).sum()
    if ss_total == 0.0:
        return 0.0
    means = np.zeros(k, dtype=np.float64)
    means[mask] = sums[mask] / counts[mask]
    ss_between = (counts * (means - grand_mean) ** 2).sum()
    return float(ss_between / ss_total)

# ── Stratified sampling efficiency ───────────────────────────────────
def _efficiency(values, labels, k, n_total, n_sample, mode):
    counts = np.bincount(labels, minlength=k).astype(np.float64)
    sums = np.bincount(labels, weights=values, minlength=k)
    sums2 = np.bincount(labels, weights=values ** 2, minlength=k)
    live = counts > 1
    N_h = counts[live]
    mean_h = sums[live] / N_h
    var_h = (sums2[live] / N_h - mean_h ** 2) * (N_h / (N_h - 1))
    W_h = N_h / n_total
    # SRS variance of the mean
    grand_var_num = ((values - values.mean()) ** 2).sum()
    S2 = grand_var_num / (n_total - 1)
    fpc_srs = 1.0 - n_sample / n_total
    var_srs = S2 / n_sample * fpc_srs
    if var_srs == 0.0:
        return 1.0
    # allocation
    if mode == "proportional":
        n_h = W_h * n_sample
    else:
        # Neyman: n_h proportional to N_h * S_h, capped at N_h
        sd_h = np.sqrt(np.maximum(var_h, 0.0))
        alloc_raw = N_h * sd_h
        alloc_sum = alloc_raw.sum()
        if alloc_sum == 0.0:
            return 1.0
        n_h = alloc_raw / alloc_sum * n_sample
        # cap strata that exceed their population size
        remaining = n_sample
        fixed = np.zeros(len(N_h), dtype=bool)
        capped = n_h > N_h
        while capped.any():
            remaining -= N_h[capped].sum()
            n_h[capped] = N_h[capped]
            fixed |= capped
            free = ~fixed
            if not free.any():
                break
            sub_raw = alloc_raw[free]
            sub_sum = sub_raw.sum()
            if sub_sum == 0.0:
                n_h[free] = remaining / free.sum()
                break
            n_h[free] = sub_raw / sub_sum * remaining
            capped = n_h > N_h
    # stratified variance of the mean
    fpc_h = 1.0 - n_h / N_h
    safe_n = np.maximum(n_h, 1.0)
    var_strat = (W_h ** 2 * var_h / safe_n * fpc_h).sum()
    if var_strat == 0.0:
        return np.inf
    return float(var_srs / var_strat)

# ── Partition metrics ────────────────────────────────────────────────
def partition_metrics(df, strata):
    strata = np.asarray(strata, dtype=np.int64)
    n = len(df)
    counts = np.bincount(strata)
    k_nonempty = int((counts > 0).sum())
    min_n = int(counts[counts > 0].min()) if k_nonempty > 0 else 0
    n_under = int((counts[(counts > 0) & (counts < MIN_STRATUM_REPORT)]).shape[0])
    k = int(counts.shape[0])
    log_fi = np.log1p(df["fi"].values).astype(np.float64)
    log_fo = np.log1p(df["fo"].values).astype(np.float64)
    log_nv = np.log1p(df["n_versions"].values).astype(np.float64)
    age = df["age_years"].values.astype(np.float64)
    result = {
        "K": k_nonempty,
        "min_n": min_n,
        "n_under_min": n_under,
        "r2_log_fi": _r2_by_strata(log_fi, strata, k),
        "r2_log_fo": _r2_by_strata(log_fo, strata, k),
        "r2_log_n_versions": _r2_by_strata(log_nv, strata, k),
        "r2_age": _r2_by_strata(age, strata, k),
        "eff_prop_log_fi": _efficiency(log_fi, strata, k, n,
                                       SAMPLE_SIZE_EXAMPLE, "proportional"),
        "eff_neyman_log_fi": _efficiency(log_fi, strata, k, n,
                                         SAMPLE_SIZE_EXAMPLE, "neyman"),
        "eff_prop_log_fo": _efficiency(log_fo, strata, k, n,
                                       SAMPLE_SIZE_EXAMPLE, "proportional"),
        "eff_neyman_log_fo": _efficiency(log_fo, strata, k, n,
                                         SAMPLE_SIZE_EXAMPLE, "neyman"),
    }
    return result

# ── Train/test split and subset R² ───────────────────────────────────
def split_halves(n, seed=SEED):
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    half = n // 2
    mask_fit = np.zeros(n, dtype=bool)
    mask_fit[perm[:half]] = True
    mask_test = ~mask_fit
    return mask_fit, mask_test
def r2_subset(df, strata, mask):
    strata = np.asarray(strata, dtype=np.int64)
    sub_strata = strata[mask]
    k = int(strata.max()) + 1 if len(strata) > 0 else 0
    log_fi = np.log1p(df["fi"].values[mask]).astype(np.float64)
    log_fo = np.log1p(df["fo"].values[mask]).astype(np.float64)
    return {
        "r2_log_fi": _r2_by_strata(log_fi, sub_strata, k),
        "r2_log_fo": _r2_by_strata(log_fo, sub_strata, k),
    }

# ── Strata table ──────────────────────────────────────────────────
def strata_table(df, strata, info, technique, config):
    strata = np.asarray(strata, dtype=np.int64)
    n = len(df)
    k = int(strata.max()) + 1 if n > 0 else 0
    log_fi = np.log1p(df["fi"].values).astype(np.float64)
    log_fo = np.log1p(df["fo"].values).astype(np.float64)
    counts = np.bincount(strata, minlength=k)
    sum_lfi = np.bincount(strata, weights=log_fi, minlength=k)
    sum_lfo = np.bincount(strata, weights=log_fo, minlength=k)
    safe = np.maximum(counts, 1)
    mean_lfi = sum_lfi / safe
    mean_lfo = sum_lfo / safe
    med = (pd.DataFrame({"_s": strata,
                         "n_versions": df["n_versions"].values.astype(np.float64),
                         "age_years": df["age_years"].values.astype(np.float64)})
           .groupby("_s").median())
    rows = []
    for _, r in info.iterrows():
        s = int(r["stratum"])
        c = int(counts[s]) if s < k else 0
        rows.append({
            "technique": technique,
            "config": config,
            "stratum": s,
            "description": r["description"],
            "n": c,
            "share": c / n if n > 0 else 0.0,
            "mean_log_fi": float(mean_lfi[s]) if s < k else 0.0,
            "mean_log_fo": float(mean_lfo[s]) if s < k else 0.0,
            "median_n_versions": float(med.loc[s, "n_versions"]) if s in med.index else 0.0,
            "median_age": float(med.loc[s, "age_years"]) if s in med.index else 0.0,
        })
    return pd.DataFrame(rows)

# ── Validation R² ─────────────────────────────────────────────────
def validation_r2(df, strata, mask_fit, mask_test):
    train = r2_subset(df, strata, mask_fit)
    test = r2_subset(df, strata, mask_test)
    return {
        "r2_log_fi_train": train["r2_log_fi"],
        "r2_log_fi_test": test["r2_log_fi"],
        "r2_log_fo_train": train["r2_log_fo"],
        "r2_log_fo_test": test["r2_log_fo"],
    }

# ── Output helpers ────────────────────────────────────────────────
def write_metrics(technique, rows):
    d = RESULTS_DIR / technique
    d.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(d / "metrics.csv", index=False)
def write_strata(technique, table):
    d = RESULTS_DIR / technique
    d.mkdir(parents=True, exist_ok=True)
    table.to_csv(d / "strata.csv", index=False)
def write_results_md(technique, text):
    d = RESULTS_DIR / technique
    d.mkdir(parents=True, exist_ok=True)
    (d / "results.md").write_text(text, encoding="utf-8")
def _fmt_num(v):
    if isinstance(v, (int, np.integer)):
        return f"{int(v):,}".replace(",", ".")
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    if "." in s:
        ipart, dpart = s.split(".")
    else:
        ipart, dpart = s, ""
    neg = ipart.startswith("-")
    digits = ipart.lstrip("-")
    ipart = f"{int(digits):,}".replace(",", ".") if digits.isdigit() else digits
    if neg:
        ipart = "-" + ipart
    return ipart + "," + dpart if dpart else ipart
def df_to_markdown(df):
    def _cell(v, col):
        if pd.isna(v):
            return "—"
        if isinstance(v, str):
            return v
        if "share" in col:
            return f"{v * 100:.1f}".replace(".", ",") + "%"
        if isinstance(v, (int, np.integer, float, np.floating)):
            return _fmt_num(v)
        return str(v)
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |",
             "| " + " | ".join("---" for _ in cols) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(_cell(row[c], c) for c in cols) + " |")
    return "\n".join(lines)

# ── Band assignment ───────────────────────────────────────────────
def assign_band(values, edges):
    values = np.asarray(values)
    edges = np.asarray(edges)
    bands = np.searchsorted(edges, values, side="right").astype(np.int32) - 1
    bands[values < edges[0]] = -1
    return bands
def band_labels(edges):
    edges = list(edges)
    labels = []
    for i in range(len(edges)):
        if i < len(edges) - 1:
            labels.append(f"{edges[i]} a {edges[i+1] - 1}")
        else:
            labels.append(f"{edges[i]} o más")
    return labels

# ── Cell partition ────────────────────────────────────────────────
def build_cell_partition(df, fi_edges, fo_edges, census,
                         census_threshold=1000):
    fi = df["fi"].values
    fo = df["fo"].values
    zc = df["zero_cell"].values
    n = len(df)
    strata = np.full(n, -1, dtype=np.int32)
    info_rows = []
    next_id = 0
    fi_bands = assign_band(fi, fi_edges)
    fo_bands = assign_band(fo, fo_edges)
    fi_lab = band_labels(fi_edges)
    fo_lab = band_labels(fo_edges)
    # census stratum
    if census:
        census_mask = fi >= census_threshold
        strata[census_mask] = next_id
        info_rows.append({"stratum": next_id, "cell": -1,
                          "fi_band": -1, "fo_band": -1,
                          "description": f"Censo (Fan-In {census_threshold} o más)"})
        next_id += 1
    else:
        census_mask = np.zeros(n, dtype=bool)
    # cell 0: isolated
    m0 = (zc == 0) & ~census_mask
    strata[m0] = next_id
    info_rows.append({"stratum": next_id, "cell": 0,
                      "fi_band": -1, "fo_band": -1,
                      "description": ZERO_CELL_NAMES[0]})
    next_id += 1
    # cell 1: consumer — bands on fo
    m1 = (zc == 1) & ~census_mask
    for b, lab in enumerate(fo_lab):
        bm = m1 & (fo_bands == b)
        if bm.any():
            strata[bm] = next_id
            info_rows.append({"stratum": next_id, "cell": 1,
                              "fi_band": -1, "fo_band": b,
                              "description": f"{ZERO_CELL_NAMES[1]}, Fan-Out {lab}"})
            next_id += 1
    # cell 2: consumed — bands on fi
    m2 = (zc == 2) & ~census_mask
    for b, lab in enumerate(fi_lab):
        bm = m2 & (fi_bands == b)
        if bm.any():
            strata[bm] = next_id
            info_rows.append({"stratum": next_id, "cell": 2,
                              "fi_band": b, "fo_band": -1,
                              "description": f"{ZERO_CELL_NAMES[2]}, Fan-In {lab}"})
            next_id += 1
    # cell 3: both — cross fi × fo
    m3 = (zc == 3) & ~census_mask
    for bi, fi_l in enumerate(fi_lab):
        for bj, fo_l in enumerate(fo_lab):
            bm = m3 & (fi_bands == bi) & (fo_bands == bj)
            if bm.any():
                strata[bm] = next_id
                info_rows.append({"stratum": next_id, "cell": 3,
                                  "fi_band": bi, "fo_band": bj,
                                  "description": f"{ZERO_CELL_NAMES[3]}, Fan-In {fi_l}, Fan-Out {fo_l}"})
                next_id += 1
    return strata, pd.DataFrame(info_rows)

# ── Merge small strata ────────────────────────────────────────────
def merge_small_strata(strata, info, min_n, mask=None):
    strata = np.asarray(strata, dtype=np.int32).copy()
    info = info.copy().reset_index(drop=True)
    # coverage: stratum → set of (fi_band, fo_band) tuples
    coverage = {}
    for _, r in info.iterrows():
        coverage[r["stratum"]] = {(int(r["fi_band"]), int(r["fo_band"]))}
    def _adjacent(s1, s2):
        for f1, o1 in coverage[s1]:
            for f2, o2 in coverage[s2]:
                if f1 == f2 and abs(o1 - o2) == 1:
                    return True
                if o1 == o2 and abs(f1 - f2) == 1:
                    return True
        return False
    def _sizes():
        s = strata[mask] if mask is not None else strata
        ids, cnts = np.unique(s, return_counts=True)
        return dict(zip(ids.tolist(), cnts.tolist()))
    while True:
        sizes = _sizes()
        # find candidates: under min_n, excluding census (cell -1) and isolated (cell 0)
        candidates = []
        for _, r in info.iterrows():
            s = r["stratum"]
            if r["cell"] in (-1, 0):
                continue
            sz = sizes.get(s, 0)
            if sz < min_n:
                candidates.append((sz, s, r["cell"]))
        if not candidates:
            break
        candidates.sort()
        merged = False
        for _, small_s, small_cell in candidates:
            neighbors = []
            for _, r in info.iterrows():
                s = r["stratum"]
                if s == small_s or r["cell"] != small_cell:
                    continue
                if _adjacent(small_s, s):
                    neighbors.append((sizes.get(s, 0), s))
            if not neighbors:
                continue
            neighbors.sort()
            _, nbr_s = neighbors[0]
            # merge small_s into nbr_s
            strata[strata == small_s] = nbr_s
            coverage[nbr_s] |= coverage.pop(small_s)
            small_desc = info.loc[info["stratum"] == small_s, "description"].values[0]
            nbr_idx = info.index[info["stratum"] == nbr_s][0]
            info.at[nbr_idx, "description"] += " + " + small_desc
            info = info[info["stratum"] != small_s].reset_index(drop=True)
            merged = True
            break
        if not merged:
            break
    # renumber consecutively from 0
    old_ids = np.sort(info["stratum"].values)
    remap = np.empty(int(old_ids.max()) + 1, dtype=np.int32)
    for new_id, old_id in enumerate(old_ids):
        remap[old_id] = new_id
    strata = remap[strata]
    info = info.sort_values("stratum").reset_index(drop=True)
    info["stratum"] = np.arange(len(info), dtype=np.int32)
    return strata, info
