"""
Exclusion candidate analysis for the npm ecosystem.
Reads raw data (pasada1, pasada2, graph_metrics, profile shards).
Caches master table as parquet to avoid reloading on each run.
Produces CSVs in analysis/.
"""
import os, json, sys, hashlib, time, re, gc
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd

BASE = "C:/Users/mvqui/Desktop/Ecosistema-npm"
OUT  = os.path.join(BASE, "analysis")
CACHE = os.path.join(OUT, "_master_cache.parquet")
CACHE_DEPS = os.path.join(OUT, "_dep_hashes_cache.parquet")
CACHE_KW = os.path.join(OUT, "_keywords_cache.parquet")
os.makedirs(OUT, exist_ok=True)

SNAPSHOT_DATE = date(2026, 9, 18)

# Copied from exploration/explore_strata.py lines 57-59
PLATFORM_RE = re.compile(
    r"(linux|darwin|win32|windows|freebsd|openbsd|netbsd|android|sunos|aix)"
    r"-(x64|x86|ia32|arm|arm64|ppc64|s390x|riscv64|loong64|mips64el|universal)")

# ── helpers ──────────────────────────────────────────────────────
def plog(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def safe_median(arr):
    a = arr[~np.isnan(arr)]
    return float(np.median(a)) if len(a) > 0 else np.nan

def rolling_median_mad(vals_arr, window):
    n = len(vals_arr)
    half = window // 2
    vals = vals_arr.astype(float)
    med = np.full(n, np.nan)
    mad = np.full(n, np.nan)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        w = vals[lo:hi]
        m = np.median(w)
        med[i] = m
        mad[i] = np.median(np.abs(w - m))
    return med, mad

def year_bucket(y):
    if pd.isna(y):
        return "no_date"
    y = int(y)
    if y < 2010:
        return "pre2010"
    return str(y)

def size_bucket(s):
    if s == 1: return "1"
    if s <= 10: return "2-10"
    if s <= 100: return "11-100"
    if s <= 1000: return "101-1000"
    return ">1000"

def fan_in_bracket(v):
    if v == 0: return "0"
    if v <= 9: return "1-9"
    if v <= 99: return "10-99"
    if v <= 999: return "100-999"
    return "1000+"

def fan_out_bracket(v):
    if v == 0: return "0"
    if v <= 2: return "1-2"
    if v <= 9: return "3-9"
    if v <= 49: return "10-49"
    return "50+"


def decompose_anomalous_days(daily_df, master_df):
    """Decompose anomalous days (dev_mad_61 > 5) with profile metrics."""
    col = "dev_mad_61"
    anom = daily_df[daily_df[col].notna() & (daily_df[col] > 5)]
    rows = []
    for _, dr in anom.iterrows():
        d = dr["created_date"]
        dev = float(dr[col])
        pkgs = master_df[master_df["created_date"] == d]
        n = len(pkgs)
        if n == 0:
            continue
        n_elig = int((pkgs["sin_version"] == 0).sum())
        pct_1ver = round(100 * (pkgs["n_versions"] == 1).sum() / n, 2)
        pct_scoped = round(100 * pkgs["scoped"].sum() / n, 2)
        pct_0_maint = round(100 * (pkgs["n_maintainers"] == 0).sum() / n, 2)
        pct_fo_0 = round(
            100 * (pkgs.loc[pkgs["sin_version"] == 0, "fan_out"] == 0).sum()
            / max(1, n_elig), 2)
        med_fc = safe_median(pkgs["file_count"].dropna().values.astype(float))
        # Largest dep-list group of the day
        hashes = pkgs.loc[pkgs["dep_list_hash"] != "", "dep_list_hash"]
        pct_top1_dep = (round(100 * hashes.value_counts().iloc[0] / n, 2)
                        if len(hashes) else 0.0)
        # Top 3 scopes of the day
        sc = pkgs.loc[pkgs["scope"] != "", "scope"]
        pct_top3_sc = (round(100 * sc.value_counts().head(3).sum() / n, 2)
                       if len(sc) else 0.0)
        # Top 5 prefix/suffix terms (non-scoped packages)
        ns = pkgs[~pkgs["scoped"] & pkgs["name"].notna()]
        if len(ns):
            parts = ns["name"].str.split("-")
            pfx = parts.str[0]
            sfx = parts.apply(lambda p: p[-1] if len(p) > 1 else "")
            tc = Counter()
            tc.update(pfx.values)
            tc.update(sfx[sfx != ""].values)
            top5 = {t for t, _ in tc.most_common(5)}
            pct_top5_ps = round(
                100 * (pfx.isin(top5) | sfx.isin(top5)).sum() / n, 2)
        else:
            pct_top5_ps = 0.0
        # Distinct exact combos
        combo = ["n_versions", "file_count", "n_keywords",
                 "has_github", "scoped", "fan_out"]
        n_combos = len(pkgs[combo].drop_duplicates())
        rows.append({
            "date": str(d), "n": n,
            "dev_mad_61": round(dev, 2),
            "exceeds_K3": dev > 3,
            "exceeds_K5": dev > 5,
            "exceeds_K10": dev > 10,
            "pct_1ver": pct_1ver,
            "pct_scoped": pct_scoped,
            "pct_0_maint": pct_0_maint,
            "pct_fo_0": pct_fo_0,
            "med_fc": med_fc,
            "pct_top1_dep_group": pct_top1_dep,
            "pct_top3_scopes": pct_top3_sc,
            "pct_top5_pfx_sfx": pct_top5_ps,
            "n_distinct_combos": n_combos,
            "uses_fan_out": True,
        })
    return pd.DataFrame(rows)


def analyze_no_maintainers(master_df, anom_date_set):
    """Analyze packages with n_maintainers == 0 as exclusion candidates."""
    m0 = master_df[master_df["n_maintainers"] == 0]
    rest = master_df[master_df["n_maintainers"] > 0]
    rows = []
    # -- year x month counts --
    hd0 = m0[m0["created_ts"].notna()]
    hd_all = master_df[master_df["created_ts"].notna()]
    ym0 = hd0.groupby(
        [hd0["created_ts"].dt.year, hd0["created_ts"].dt.month]
    ).size()
    ym_all = hd_all.groupby(
        [hd_all["created_ts"].dt.year, hd_all["created_ts"].dt.month]
    ).size()
    for (y, mo), cnt in ym0.items():
        total = int(ym_all.get((y, mo), 0))
        pct = round(100 * cnt / total, 2) if total else 0
        rows.append({"section": "year_month", "key1": str(int(y)),
                     "key2": f"{int(mo):02d}", "label": "n_0maint",
                     "value": int(cnt), "uses_fan_out": False})
        rows.append({"section": "year_month", "key1": str(int(y)),
                     "key2": f"{int(mo):02d}", "label": "pct_0maint",
                     "value": pct, "uses_fan_out": False})
    # -- profile comparison by year --
    for yc in sorted(master_df["year_cat"].unique()):
        for glabel, sub in [("0_maint", m0[m0["year_cat"] == yc]),
                            ("rest", rest[rest["year_cat"] == yc])]:
            n = len(sub)
            if n == 0:
                continue
            elig = sub[sub["sin_version"] == 0]
            vals = {
                "med_n_versions": safe_median(
                    sub["n_versions"].values.astype(float)),
                "med_file_count": safe_median(
                    sub["file_count"].dropna().values.astype(float)),
                "med_fan_out": (safe_median(
                    elig["fan_out"].values.astype(float))
                    if len(elig) else np.nan),
                "pct_scoped": round(100 * sub["scoped"].sum() / n, 2),
                "med_dep_group_size": safe_median(
                    sub["dep_group_size"].values.astype(float)),
            }
            for lbl, v in vals.items():
                rows.append({
                    "section": "profile", "key1": glabel, "key2": yc,
                    "label": lbl,
                    "value": None if pd.isna(v) else round(v, 4),
                    "uses_fan_out": lbl == "med_fan_out",
                })
    # -- overlap with anomalous days from section A --
    total_on_anom = 0
    for d in sorted(anom_date_set):
        day_all = master_df[master_df["created_date"] == d]
        day_m0 = day_all[day_all["n_maintainers"] == 0]
        nt = len(day_all)
        nm = len(day_m0)
        total_on_anom += nm
        pct = round(100 * nm / nt, 2) if nt else 0
        rows.append({"section": "anom_overlap", "key1": str(d), "key2": "",
                     "label": "n_day_total", "value": nt,
                     "uses_fan_out": False})
        rows.append({"section": "anom_overlap", "key1": str(d), "key2": "",
                     "label": "n_0maint", "value": nm,
                     "uses_fan_out": False})
        rows.append({"section": "anom_overlap", "key1": str(d), "key2": "",
                     "label": "pct_0maint", "value": pct,
                     "uses_fan_out": False})
    rows.append({"section": "anom_overlap", "key1": "__TOTAL__", "key2": "",
                 "label": "n_0maint_on_anom_days", "value": total_on_anom,
                 "uses_fan_out": False})
    # -- top 20 days with most 0-maintainer packages --
    day_counts = m0[m0["created_ts"].notna()].groupby("created_date").size()
    for d, cnt in day_counts.nlargest(20).items():
        rows.append({"section": "top20_days", "key1": str(d), "key2": "",
                     "label": "n_0maint", "value": int(cnt),
                     "uses_fan_out": False})
    return pd.DataFrame(rows)


def top_combos_by_year(master_df):
    """Top 20 (n_versions, file_count, n_keywords, has_github, scoped, fan_out) combos per year."""
    combo_cols = ["n_versions", "file_count", "n_keywords",
                  "has_github", "scoped", "fan_out"]
    rows = []
    for yc in sorted(master_df["year_cat"].unique()):
        sub = master_df[master_df["year_cat"] == yc]
        n = len(sub)
        if n == 0:
            continue
        # file_count coverage
        n_fc = int(sub["file_count"].notna().sum())
        fc_avail = round(n_fc / n, 4)
        fc_low = fc_avail < 0.9
        # Group combos — sentinel for NaN file_count
        tmp = sub[combo_cols].copy()
        tmp["file_count"] = tmp["file_count"].fillna(-1)
        grp = tmp.groupby(combo_cols).size().reset_index(name="count")
        grp = grp.sort_values("count", ascending=False).reset_index(drop=True)
        # HHI over all distinct combos
        hhi = round(float(np.sum((grp["count"].values / n) ** 2)), 6)
        # Top 20
        for rank, (_, r) in enumerate(grp.head(20).iterrows()):
            fc_val = r["file_count"]
            rows.append({
                "year": yc, "rank": rank + 1,
                "n_versions": int(r["n_versions"]),
                "file_count": None if fc_val < 0 else int(fc_val),
                "n_keywords": int(r["n_keywords"]),
                "has_github": bool(r["has_github"]),
                "scoped": bool(r["scoped"]),
                "fan_out": int(r["fan_out"]),
                "count": int(r["count"]),
                "pct": round(100 * int(r["count"]) / n, 2),
                "hhi": hhi,
                "n_total": n,
                "n_distinct_combos": len(grp),
                "fc_available": fc_avail,
                "fc_low_coverage": fc_low,
                "uses_fan_out": True,
            })
    return pd.DataFrame(rows)


def emergent_name_families(master_df):
    """Detect prefix/suffix families concentrated in a single year."""
    R_GRID = [5, 10, 50]
    M_GRID = [500, 1000, 3000]
    MIN_M = min(M_GRID)
    cols = ["name", "year_cat", "scoped", "n_versions", "has_github",
            "n_maintainers", "created_date"]
    df = master_df.loc[master_df["name"].notna(), cols].copy()
    # Bare name: strip scope prefix for scoped packages
    sc_mask = df["name"].str.startswith("@") & df["name"].str.contains("/")
    bare = df["name"].where(~sc_mask, df["name"].str.split("/").str[1])
    parts = bare.str.split("-")
    df["_pfx"] = parts.str[0]
    df["_sfx"] = parts.apply(lambda p: p[-1] if len(p) > 1 else "")
    rows = []
    for kind, col in [("prefix", "_pfx"), ("suffix", "_sfx")]:
        valid = df[df[col] != ""]
        yr_counts = valid.groupby(["year_cat", col]).size()
        total_counts = valid.groupby(col).size()
        big_enough = yr_counts[yr_counts >= MIN_M]
        profiles = {}
        for (yc, term), cnt_yr in big_enough.items():
            cnt_others = total_counts[term] - cnt_yr
            passing = [(R, M) for R in R_GRID for M in M_GRID
                       if cnt_yr >= M
                       and (cnt_others == 0 or cnt_yr >= R * cnt_others)]
            if not passing:
                continue
            key = (kind, term, yc)
            if key not in profiles:
                sub = valid[(valid["year_cat"] == yc) & (valid[col] == term)]
                n = len(sub)
                dates = sub["created_date"].dropna()
                if len(dates):
                    d_min, d_max = min(dates), max(dates)
                    wd = (d_max - d_min).days
                else:
                    d_min = d_max = None
                    wd = None
                profiles[key] = {
                    "n": n,
                    "first": str(d_min) if d_min else None,
                    "last": str(d_max) if d_max else None,
                    "window_days": wd,
                    "pct_1ver": round(
                        100 * (sub["n_versions"] == 1).sum() / n, 2),
                    "pct_has_github": round(
                        100 * sub["has_github"].sum() / n, 2),
                    "pct_scoped": round(
                        100 * sub["scoped"].sum() / n, 2),
                    "pct_0_maint": round(
                        100 * (sub["n_maintainers"] == 0).sum() / n, 2),
                }
            prof = profiles[key]
            for R, M in passing:
                rows.append({"kind": kind, "term": term, "year": yc,
                             "R": R, "M": M, **prof})
    return pd.DataFrame(rows)


def group_profiles_and_keywords(master_df, enf_df, kw_df):
    """Profile families/scopes and keyword analysis by year."""
    rows = []

    def _prof(sub):
        n = len(sub)
        if n == 0:
            return {}
        return {
            "n": n,
            "med_n_versions": safe_median(sub["n_versions"].values.astype(float)),
            "pct_2plus_ver": round(100 * (sub["n_versions"] >= 2).sum() / n, 2),
            "pct_has_github": round(100 * sub["has_github"].sum() / n, 2),
            "pct_has_keywords": round(100 * (sub["n_keywords"] > 0).sum() / n, 2),
            "pct_fi_gt0": round(100 * (sub["fan_in"] > 0).sum() / n, 2),
            "pct_0_maint": round(100 * (sub["n_maintainers"] == 0).sum() / n, 2),
        }

    def _emit(sec, k1, k2, k3, prof):
        for lbl, v in prof.items():
            rows.append({"section": sec, "key1": k1, "key2": k2,
                         "key3": k3, "label": lbl,
                         "value": None if pd.isna(v) else v})

    # -- Family profiles from D --
    named = master_df[master_df["name"].notna()]
    sc_m = named["name"].str.startswith("@") & named["name"].str.contains("/")
    bare = named["name"].where(~sc_m, named["name"].str.split("/").str[1])
    parts = bare.str.split("-")
    pfx_s = parts.str[0]
    sfx_s = parts.apply(lambda p: p[-1] if len(p) > 1 else "")
    if len(enf_df):
        for _, fk in enf_df[["kind", "term", "year"]].drop_duplicates().iterrows():
            col_s = pfx_s if fk["kind"] == "prefix" else sfx_s
            mask = (named["year_cat"] == fk["year"]) & (col_s == fk["term"])
            p = _prof(named[mask])
            if p:
                _emit("family_profile", fk["kind"], fk["term"], fk["year"], p)

    # -- Top 30 scopes per year --
    for yc in sorted(master_df["year_cat"].unique()):
        sc_yr = master_df[(master_df["year_cat"] == yc) & (master_df["scope"] != "")]
        if len(sc_yr) == 0:
            continue
        for sc in sc_yr["scope"].value_counts().head(30).index:
            p = _prof(sc_yr[sc_yr["scope"] == sc])
            if p:
                _emit("scope_profile", sc, yc, "", p)

    # -- Top 30 keywords per year --
    kw_yr = kw_df.merge(master_df[["name", "year_cat"]], on="name", how="inner")
    for yc in sorted(kw_yr["year_cat"].unique()):
        sub = kw_yr[kw_yr["year_cat"] == yc]
        n_pkg = int((master_df["year_cat"] == yc).sum())
        for rank, (kw, cnt) in enumerate(sub["keyword"].value_counts().head(30).items()):
            rows.append({"section": "top30_kw", "key1": yc, "key2": kw,
                         "key3": str(rank + 1), "label": "count",
                         "value": int(cnt)})
            rows.append({"section": "top30_kw", "key1": yc, "key2": kw,
                         "key3": str(rank + 1), "label": "pct",
                         "value": round(100 * cnt / max(1, n_pkg), 2)})

    # -- Keyword growth year-over-year --
    kw_ct = kw_yr.groupby(["year_cat", "keyword"]).size().reset_index(name="count")
    num_yrs = sorted(y for y in kw_ct["year_cat"].unique() if y.isdigit())
    for i in range(1, len(num_yrs)):
        yp, yc = num_yrs[i - 1], num_yrs[i]
        prev = kw_ct[kw_ct["year_cat"] == yp].set_index("keyword")["count"]
        cur = kw_ct[kw_ct["year_cat"] == yc].set_index("keyword")["count"]
        both = pd.DataFrame({"prev": prev, "cur": cur}).dropna()
        both = both[both["prev"] > 0]
        both["ratio"] = both["cur"] / both["prev"]
        for rank, (kw, r) in enumerate(both.nlargest(30, "ratio").iterrows()):
            rows.append({"section": "kw_growth", "key1": yc, "key2": kw,
                         "key3": str(rank + 1), "label": "count_prev",
                         "value": int(r["prev"])})
            rows.append({"section": "kw_growth", "key1": yc, "key2": kw,
                         "key3": str(rank + 1), "label": "count_cur",
                         "value": int(r["cur"])})
            rows.append({"section": "kw_growth", "key1": yc, "key2": kw,
                         "key3": str(rank + 1), "label": "growth_ratio",
                         "value": round(float(r["ratio"]), 2)})

    return pd.DataFrame(rows)


def build_exclusion_summary(master_df, candidate_defs):
    """Summary tables for all exclusion candidate indicators."""
    rows = []
    col_names = [c for c, _ in candidate_defs]
    fi_bkt = master_df["fan_in"].apply(fan_in_bracket)
    fo_bkt = master_df["fan_out"].apply(fan_out_bracket)
    fo_elig = master_df["sin_version"] == 0
    fi_order = ["0", "1-9", "10-99", "100-999", "1000+"]
    fo_order = ["0", "1-2", "3-9", "10-49", "50+"]

    for col, ufo in candidate_defs:
        mask = master_df[col]
        rows.append({"section": "total", "candidate": col,
                     "key1": "", "key2": "", "label": "n_flagged",
                     "value": int(mask.sum()), "uses_fan_out": ufo})
        for yc in sorted(master_df["year_cat"].unique()):
            n = int((mask & (master_df["year_cat"] == yc)).sum())
            rows.append({"section": "by_year", "candidate": col,
                         "key1": yc, "key2": "", "label": "n_flagged",
                         "value": n, "uses_fan_out": ufo})
        for bk in fi_order:
            n = int((mask & (fi_bkt == bk)).sum())
            rows.append({"section": "by_fan_in", "candidate": col,
                         "key1": bk, "key2": "", "label": "n_flagged",
                         "value": n, "uses_fan_out": ufo})
        for bk in fo_order:
            n = int((mask & fo_elig & (fo_bkt == bk)).sum())
            rows.append({"section": "by_fan_out", "candidate": col,
                         "key1": bk, "key2": "", "label": "n_flagged",
                         "value": n, "uses_fan_out": ufo})
        for other, _ in candidate_defs:
            if other == col:
                continue
            n = int((mask & master_df[other]).sum())
            rows.append({"section": "overlap", "candidate": col,
                         "key1": other, "key2": "", "label": "n_both",
                         "value": n, "uses_fan_out": ufo})

    detail_df = pd.DataFrame(rows)

    n_cands = master_df[col_names].sum(axis=1).astype(int)
    ct_rows = []
    for yc in sorted(master_df["year_cat"].unique()):
        vc = n_cands[master_df["year_cat"] == yc].value_counts().sort_index()
        for nc, n_pkg in vc.items():
            ct_rows.append({"year": yc, "n_candidates": int(nc),
                            "n_packages": int(n_pkg)})
    counts_df = pd.DataFrame(ct_rows)

    return detail_df, counts_df


# ═══════════════════════════════════════════════════════════════════
#  PHASE 0: LOAD OR BUILD MASTER TABLE
# ═══════════════════════════════════════════════════════════════════

# Cache version: bump to invalidate when build logic changes
_CACHE_VERSION = "v3_keep_default_na"
_CACHE_FLAG = os.path.join(OUT, f"_cache_{_CACHE_VERSION}")

if os.path.exists(CACHE) and os.path.exists(CACHE_DEPS) and os.path.exists(_CACHE_FLAG):
    plog("Cache found — loading master table from parquet ...")
    master = pd.read_parquet(CACHE)
    dep_hashes_df = pd.read_parquet(CACHE_DEPS)
    # Rebuild dep_hash_map and hash_counter from cache
    dep_hash_map = dict(zip(dep_hashes_df["name"], dep_hashes_df["dep_list_hash"]))
    hash_counter = Counter(dep_hash_map.values())
    # Rebuild node_set
    node_set = set(master["name"].values)
    plog(f"  Loaded: {len(master):,} rows, {len(dep_hashes_df):,} dep hashes")
else:
    if os.path.exists(CACHE) and not os.path.exists(_CACHE_FLAG):
        plog("Stale cache detected — rebuilding ...")
    else:
        plog("No cache — building master table from raw data ...")

    # ── 0a. graph_metrics ────────────────────────────────────────
    plog("  Loading graph_metrics.csv ...")
    gm = pd.read_csv(
        os.path.join(BASE, "data/03_dependency_graph/graph_metrics.csv"),
        usecols=["paquete", "fan_in", "fan_out", "sin_version"],
        dtype={"paquete": str, "fan_in": "int32", "fan_out": "int32",
               "sin_version": "int8"},
        keep_default_na=False, na_values=[],
    )
    gm.rename(columns={"paquete": "name"}, inplace=True)
    # Report empty/blank names
    blank_mask = (gm["name"] == "") | gm["name"].isna()
    n_blank = int(blank_mask.sum())
    if n_blank:
        plog(f"    WARNING: {n_blank} rows with empty name in graph_metrics:")
        for _, r in gm[blank_mask].head(5).iterrows():
            plog(f"      name={r['name']!r} fan_in={r['fan_in']} fan_out={r['fan_out']}")
    node_set = set(gm["name"].values)
    plog(f"    {len(gm):,} nodes ({n_blank} blank)")

    # ── 0b. pasada2 shards ──────────────────────────────────────
    plog("  Loading pasada2 shards (dep lists only) ...")
    p2_dir = os.path.join(BASE, "data/pasada2")
    p2_files = sorted(f for f in os.listdir(p2_dir) if f.endswith(".jsonl"))

    p2_deps = {}

    for fi, fname in enumerate(p2_files):
        with open(os.path.join(p2_dir, fname), encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                if "error" in rec or "sin_version" in rec:
                    continue
                deps = rec.get("deps", [])
                norm_deps = [d.strip().lower() for d in deps]
                if norm_deps:
                    p2_deps[rec["name"].strip().lower()] = norm_deps
        if (fi + 1) % 20 == 0 or fi + 1 == len(p2_files):
            plog(f"    pasada2: {fi+1}/{len(p2_files)}")

    plog(f"    done: {len(p2_deps):,} packages with deps")

    # ── 0c. profile shards ──────────────────────────────────────
    plog("  Loading profile shards ...")
    prof_dirs = [
        os.path.join(BASE, "data/04_profile/part1"),
        os.path.join(BASE, "data/04_profile/part2"),
    ]
    prof_records = []
    total_shards = 0
    for pd_dir in prof_dirs:
        if not os.path.isdir(pd_dir):
            continue
        files = sorted(f for f in os.listdir(pd_dir) if f.endswith(".jsonl"))
        for fi, fname in enumerate(files):
            with open(os.path.join(pd_dir, fname), encoding="utf-8") as fh:
                for line in fh:
                    rec = json.loads(line)
                    prof_records.append({
                        "name": rec["name"],
                        "created": rec.get("created", ""),
                        "n_versions": int(rec.get("n_versions", 0)),
                        "n_maintainers": int(rec.get("n_maintainers", 0)),
                        "n_keywords": int(rec.get("n_keywords", 0)),
                        "has_github": rec.get("has_github", "False") in (True, "True"),
                        "file_count": rec.get("file_count"),
                        "deprecated": rec.get("deprecated", "False") in (True, "True"),
                    })
            total_shards += 1
            if total_shards % 20 == 0 or (fi + 1 == len(files) and pd_dir == prof_dirs[-1]):
                plog(f"    profile: {total_shards} shards, {len(prof_records):,} records")

    plog(f"    done: {len(prof_records):,} records")
    prof = pd.DataFrame(prof_records)
    del prof_records; gc.collect()

    # Parse dates
    plog("  Parsing dates ...")
    def parse_created(s):
        if not s or s == "None" or pd.isna(s):
            return pd.NaT
        try:
            return pd.Timestamp(s[:19])
        except Exception:
            return pd.NaT

    prof["created_ts"] = prof["created"].apply(parse_created)
    prof["created_date"] = prof["created_ts"].dt.date
    prof["created_year"] = prof["created_ts"].dt.year.astype("Int32")
    prof["file_count"] = pd.to_numeric(prof["file_count"], errors="coerce")

    # Dedup profile
    prof_dedup = prof.drop_duplicates(subset="name", keep="first")
    plog(f"    dedup: {len(prof_dedup):,} (dropped {len(prof) - len(prof_dedup):,})")
    del prof

    # ── 0d. Merge ───────────────────────────────────────────────
    plog("  Merging ...")
    master = gm.merge(
        prof_dedup[["name", "created_ts", "created_date", "created_year",
                     "n_versions", "n_maintainers", "n_keywords",
                     "has_github", "file_count", "deprecated"]],
        on="name", how="left",
    )
    del gm, prof_dedup; gc.collect()

    master["scoped"] = master["name"].str.startswith("@")

    # ── 0e. Dangling ────────────────────────────────────────────
    plog("  Computing dangling ...")
    n_missing_map = {}
    for nm, deps in p2_deps.items():
        n_missing_map[nm] = sum(1 for d in deps if d not in node_set)

    master["n_deps_missing"] = master["name"].map(n_missing_map).fillna(0).astype("int32")
    fo = master["fan_out"].values.astype(float)
    nmiss = master["n_deps_missing"].values.astype(float)
    master["dangling_share"] = np.where(fo > 0, nmiss / fo, 0.0)

    # ── 0f. Dep-list hashes ─────────────────────────────────────
    plog("  Computing dep-list hashes ...")
    dep_hash_map = {}
    for nm, deps in p2_deps.items():
        key = ",".join(sorted(deps))
        dep_hash_map[nm] = hashlib.md5(key.encode()).hexdigest()[:16]

    hash_counter = Counter(dep_hash_map.values())
    dep_group_size = {nm: hash_counter[h] for nm, h in dep_hash_map.items()}
    master["dep_list_hash"] = master["name"].map(dep_hash_map).fillna("")
    master["dep_group_size"] = master["name"].map(dep_group_size).fillna(0).astype("int32")

    # year category
    master["year_cat"] = master["created_year"].apply(year_bucket)

    # scope
    def get_scope(name):
        if not isinstance(name, str):
            return ""
        if name.startswith("@"):
            slash = name.find("/")
            if slash > 0:
                return name[:slash]
        return ""
    master["scope"] = master["name"].apply(get_scope)

    # ── 0g. Save cache ──────────────────────────────────────────
    plog("  Saving cache ...")
    master.to_parquet(CACHE, index=False)
    dep_hashes_df = pd.DataFrame(list(dep_hash_map.items()), columns=["name", "dep_list_hash"])
    dep_hashes_df.to_parquet(CACHE_DEPS, index=False)

    del p2_deps, n_missing_map, dep_group_size
    gc.collect()

    # Write version flag so stale caches are rebuilt
    with open(_CACHE_FLAG, "w") as f:
        f.write(_CACHE_VERSION)
    plog(f"  Cache saved ({_CACHE_VERSION}).")

# ── 0h. Keywords cache ──────────────────────────────────────────
if os.path.exists(CACHE_KW):
    plog("Keywords cache found — loading ...")
    kw_cache = pd.read_parquet(CACHE_KW)
    plog(f"  Loaded: {len(kw_cache):,} (name, keyword) pairs")
else:
    plog("Building keywords cache from profile shards ...")
    kw_records = []
    _kw_dirs = [
        os.path.join(BASE, "data/04_profile/part1"),
        os.path.join(BASE, "data/04_profile/part2"),
    ]
    _seen = set()
    for _kd in _kw_dirs:
        if not os.path.isdir(_kd):
            continue
        for _fn in sorted(f for f in os.listdir(_kd) if f.endswith(".jsonl")):
            with open(os.path.join(_kd, _fn), encoding="utf-8") as fh:
                for line in fh:
                    rec = json.loads(line)
                    nm = rec["name"]
                    if nm in _seen:
                        continue
                    _seen.add(nm)
                    normed = set()
                    for kw in rec.get("keywords") or []:
                        if isinstance(kw, str):
                            k = kw.strip().lower()
                            if k:
                                normed.add(k)
                    for k in normed:
                        kw_records.append({"name": nm, "keyword": k})
    kw_cache = pd.DataFrame(kw_records)
    del kw_records, _seen; gc.collect()
    kw_cache.to_parquet(CACHE_KW, index=False)
    plog(f"  Keywords cache saved: {len(kw_cache):,} pairs")

# ── Consistency ──────────────────────────────────────────────────
n_nodes = len(master)
n_with_profile = master["created_year"].notna().sum()
n_spam = int(((master["dangling_share"] > 0.5) & (master["fan_out"] >= 10)).sum())
n_sinver = int(master["sin_version"].sum())
plog(f"CONSISTENCY: nodes={n_nodes:,} (exp 4,395,451)  "
     f"profile={n_with_profile:,} (exp 4,389,236)  "
     f"spam_suspect={n_spam:,} (exp 15,540)  "
     f"sin_version={n_sinver:,}")

# Ensure needed columns exist
if "year_cat" not in master.columns:
    master["year_cat"] = master["created_year"].apply(year_bucket)
if "scope" not in master.columns:
    master["scope"] = master["name"].apply(
        lambda n: n[:n.find("/")] if isinstance(n, str) and n.startswith("@") and "/" in n else "")
if "scoped" not in master.columns:
    master["scoped"] = master["name"].str.startswith("@")
if "created_date" not in master.columns:
    master["created_date"] = master["created_ts"].dt.date

plog(f"Ready. {len(master):,} rows.\n")

# ═══════════════════════════════════════════════════════════════════
#  PART 1: TIME AND PROFILE
# ═══════════════════════════════════════════════════════════════════
plog("=" * 60)
plog("PART 1: TIME AND PROFILE")
plog("=" * 60)

has_date = master[master["created_ts"].notna()].copy()
plog(f"Packages with date: {len(has_date):,}")

# ── 1.1 Year x Month ────────────────────────────────────────────
plog("1.1 Year x Month table ...")
ym_counts = has_date.groupby(
    [has_date["created_year"], has_date["created_ts"].dt.month]
).size()
ym_pivot = ym_counts.unstack(fill_value=0)
ym_pivot.columns = [f"M{m:02d}" for m in ym_pivot.columns]
ym_pivot["total"] = ym_pivot.sum(axis=1)
ym_pivot.index.name = "year"
ym_pivot.to_csv(os.path.join(OUT, "p1_year_month.csv"))
plog("  -> p1_year_month.csv")

# ── 1.1b Daily counts ───────────────────────────────────────────
plog("1.1b Daily counts + rolling stats ...")
raw_daily = has_date.groupby("created_date").size().reset_index(name="n")
raw_daily["date"] = pd.to_datetime(raw_daily["created_date"])
raw_daily = raw_daily.sort_values("date").reset_index(drop=True)

# Inspect tail and snapshot cutoff
plog("  Last 10 days of raw series:")
for _, r in raw_daily.tail(10).iterrows():
    plog(f"    {r['date'].strftime('%Y-%m-%d')}  n={int(r['n'])}")

# Detect post-snapshot drop: sharp drop after SNAPSHOT_DATE
BURST_CUTOFF = pd.Timestamp(SNAPSHOT_DATE)
post = raw_daily[raw_daily["date"] > BURST_CUTOFF]
pre_last5 = raw_daily[(raw_daily["date"] <= BURST_CUTOFF) &
                       (raw_daily["date"] >= BURST_CUTOFF - pd.Timedelta(days=5))]
avg_pre = pre_last5["n"].mean() if len(pre_last5) else 0
avg_post = post["n"].mean() if len(post) else 0
plog(f"  Avg 5d before snapshot: {avg_pre:.0f}, avg post-snapshot: {avg_post:.0f}")
plog(f"  Post-snapshot packages: {int(post['n'].sum()):,} in {len(post)} days")
plog(f"  -> Cutting burst series at {SNAPSHOT_DATE} (post-snapshot reported separately)")

# Save full raw daily (including post-snapshot) for reference
raw_daily["year"] = raw_daily["date"].dt.year
raw_daily["post_snapshot"] = raw_daily["date"] > BURST_CUTOFF
raw_daily.to_csv(os.path.join(OUT, "p1_daily_counts_raw.csv"), index=False)
plog("  -> p1_daily_counts_raw.csv (full series with post_snapshot flag)")

# Build analysis series: 2011-01-01 to SNAPSHOT_DATE, zero-filled calendar
SERIES_START = pd.Timestamp("2011-01-01")
calendar = pd.DataFrame({"date": pd.date_range(SERIES_START, BURST_CUTOFF, freq="D")})
daily = calendar.merge(
    raw_daily[["date", "n"]],
    on="date", how="left",
)
daily["n"] = daily["n"].fillna(0).astype(int)
daily["year"] = daily["date"].dt.year
daily["created_date"] = daily["date"].dt.date
plog(f"  Analysis series: {len(daily):,} days ({SERIES_START.date()} to {SNAPSHOT_DATE}), zero-filled")

# Packages outside the analysis window (pre-2011 + post-snapshot)
pre2011 = raw_daily[(raw_daily["date"] < SERIES_START) & ~raw_daily["post_snapshot"]]
plog(f"  Pre-2011 packages excluded from rolling: {int(pre2011['n'].sum()):,} "
     f"({len(pre2011)} days, years {sorted(pre2011['year'].unique())})")

# Rolling stats on clean series
for w in [31, 61, 91]:
    plog(f"  rolling window {w} ...")
    med, mad = rolling_median_mad(daily["n"].values, w)
    daily[f"med_{w}"] = med
    daily[f"mad_{w}"] = mad
    with np.errstate(divide="ignore", invalid="ignore"):
        daily[f"dev_mad_{w}"] = np.where(mad > 0, (daily["n"].values - med) / mad, np.nan)

daily.to_csv(os.path.join(OUT, "p1_daily_counts.csv"), index=False)
plog("  -> p1_daily_counts.csv")

# ── 1.1c Anomalous days grid ────────────────────────────────────
plog("1.1c Anomalous days grid ...")
anom_rows = []
for w in [31, 61, 91]:
    dc = f"dev_mad_{w}"
    for K in [3, 5, 10]:
        for yr in sorted(daily["year"].unique()):
            sub = daily[(daily["year"] == yr) & daily[dc].notna()]
            anom = sub[sub[dc] > K]
            yr_total = int(daily[daily["year"] == yr]["n"].sum())
            anom_pkgs = int(anom["n"].sum())
            anom_rows.append({
                "window": w, "K": K, "year": yr,
                "anom_days": len(anom), "anom_pkgs": anom_pkgs,
                "year_total": yr_total,
                "pct": round(100 * anom_pkgs / yr_total, 2) if yr_total else 0,
            })

pd.DataFrame(anom_rows).to_csv(os.path.join(OUT, "p1_anomalous_days_grid.csv"), index=False)
plog("  -> p1_anomalous_days_grid.csv")

# ── 1.1d Top 20 days ────────────────────────────────────────────
top20 = daily.nlargest(20, "n")[["date", "n", "year"]].copy()
top20["date"] = top20["date"].dt.strftime("%Y-%m-%d")
top20.to_csv(os.path.join(OUT, "p1_top20_days.csv"), index=False)
plog(f"  -> p1_top20_days.csv  (top: {top20.iloc[0]['date']} = {top20.iloc[0]['n']:,})")

# ── 1.1e Anomalous days decomposed ──────────────────────────────
plog("1.1e Anomalous days decomposed ...")
anom_dec = decompose_anomalous_days(daily, master)
anom_dec.to_csv(os.path.join(OUT, "p1_anomalous_days_decomposed.csv"), index=False)
plog(f"  -> p1_anomalous_days_decomposed.csv ({len(anom_dec)} days)")

# ── 1.2 Profile by year ─────────────────────────────────────────
plog("1.2 Profile by year ...")
prof_rows = []
years_sorted = sorted(master["year_cat"].unique())
for i, yc in enumerate(years_sorted):
    sub = master[master["year_cat"] == yc]
    n = len(sub)
    with_fc = int(sub["file_count"].notna().sum())
    prof_rows.append({
        "year": yc, "packages": n,
        "pct_1ver": round(100 * (sub["n_versions"] == 1).sum() / n, 2) if n else 0,
        "pct_scoped": round(100 * sub["scoped"].sum() / n, 2) if n else 0,
        "pct_has_github": round(100 * sub["has_github"].sum() / n, 2) if n else 0,
        "pct_no_keywords": round(100 * (sub["n_keywords"] == 0).sum() / n, 2) if n else 0,
        "pct_0_maint": round(100 * (sub["n_maintainers"] == 0).sum() / n, 2) if n else 0,
        "pct_fi_0": round(100 * (sub["fan_in"] == 0).sum() / n, 2) if n else 0,
        "n_sin_version": int(sub["sin_version"].sum()),
        "n_fo_eligible": int((sub["sin_version"] == 0).sum()),
        "pct_fo_0": round(100 * (sub.loc[sub["sin_version"] == 0, "fan_out"] == 0).sum()
                          / max(1, (sub["sin_version"] == 0).sum()), 2),
        "med_nver": safe_median(sub["n_versions"].values.astype(float)),
        "med_fo": safe_median(sub.loc[sub["sin_version"] == 0, "fan_out"].values.astype(float)),
        "med_fc": safe_median(sub["file_count"].dropna().values.astype(float)),
        "n_with_fc": with_fc,
    })
    if (i + 1) % 5 == 0:
        plog(f"    {i+1}/{len(years_sorted)} years")

prof_yr = pd.DataFrame(prof_rows)
prof_yr.to_csv(os.path.join(OUT, "p1_profile_by_year.csv"), index=False)
plog("  -> p1_profile_by_year.csv")

# ── 1.3 No-maintainer packages ──────────────────────────────────
plog("1.3 No-maintainer packages ...")
anom_date_set = set(
    daily.loc[daily["dev_mad_61"].notna() & (daily["dev_mad_61"] > 5),
              "created_date"]
)
nm_df = analyze_no_maintainers(master, anom_date_set)
nm_df.to_csv(os.path.join(OUT, "p1_no_maintainers.csv"), index=False)
plog(f"  -> p1_no_maintainers.csv ({len(nm_df)} rows)")

plog("PART 1 DONE.\n")

# ═══════════════════════════════════════════════════════════════════
#  PART 2: DUPLICATION, FINGERPRINTS, SCOPES, NAMES
# ═══════════════════════════════════════════════════════════════════
plog("=" * 60)
plog("PART 2: DUPLICATION, FINGERPRINTS, SCOPES, NAMES")
plog("=" * 60)

# ── 2.4 Dep-list groups by year ─────────────────────────────────
plog("2.4 Dep-list groups by year ...")
has_deps = master[(master["dep_list_hash"] != "") & (master["fan_out"] > 0)].copy()
plog(f"  {len(has_deps):,} packages with >=1 dep")

plog("  within-year group sizes ...")
yr_hash_sz = has_deps.groupby(["year_cat", "dep_list_hash"]).size().reset_index(name="yr_grp_sz")
has_deps = has_deps.merge(yr_hash_sz, on=["year_cat", "dep_list_hash"], how="left")

dep_yr_rows = []
year_cats = sorted(has_deps["year_cat"].unique())
for i, yc in enumerate(year_cats):
    sub = has_deps[has_deps["year_cat"] == yc]
    n = len(sub)
    if n == 0: continue
    for label, col in [("universe", "dep_group_size"), ("within_year", "yr_grp_sz")]:
        bkts = sub[col].apply(size_bucket).value_counts()
        for bk in ["1", "2-10", "11-100", "101-1000", ">1000"]:
            cnt = int(bkts.get(bk, 0))
            dep_yr_rows.append({"year": yc, "scope": label, "bucket": bk,
                                "packages": cnt, "pct": round(100*cnt/n, 2)})
    # concentration
    top10 = sub.groupby("dep_list_hash")["yr_grp_sz"].first().nlargest(10)
    t10_sum = int(top10.sum())
    grp_sz = sub.groupby("dep_list_hash").size()
    hhi = float(np.sum((grp_sz.values / n) ** 2))
    dep_yr_rows.append({"year": yc, "scope": "concentration", "bucket": "top10_pct",
                         "packages": t10_sum, "pct": round(100*t10_sum/n, 2)})
    dep_yr_rows.append({"year": yc, "scope": "concentration", "bucket": "HHI",
                         "packages": 0, "pct": round(hhi, 6)})
    if (i+1) % 5 == 0:
        plog(f"    {i+1}/{len(year_cats)} years")

pd.DataFrame(dep_yr_rows).to_csv(os.path.join(OUT, "p2_dep_groups_by_year.csv"), index=False)
plog("  -> p2_dep_groups_by_year.csv")
del has_deps, yr_hash_sz; gc.collect()

# ── 2.5 Exact fingerprints by year ──────────────────────────────
plog("2.5 Fingerprints by year ...")
fp_rows = []
for var, col in [("file_count", "file_count"), ("n_keywords", "n_keywords"),
                 ("fan_out", "fan_out")]:
    for yc in years_sorted:
        sub = master[master["year_cat"] == yc]
        if var == "file_count":
            vals = sub[col].dropna()
        elif var == "fan_out":
            vals = sub.loc[sub["sin_version"] == 0, col]
        else:
            vals = sub[col]
        n = len(vals)
        if n == 0: continue
        vc = vals.value_counts()
        top10 = vc.head(10)
        for rank, (val, cnt) in enumerate(top10.items()):
            fp_rows.append({"variable": var, "year": yc, "rank": rank+1,
                            "value": val, "count": int(cnt), "pct": round(100*cnt/n, 2)})
        # summary row: HHI
        hhi = float(np.sum((vc.values / n) ** 2))
        fp_rows.append({"variable": var, "year": yc, "rank": 0,
                         "value": "SUMMARY", "count": n, "pct": round(hhi, 6)})

pd.DataFrame(fp_rows).to_csv(os.path.join(OUT, "p2_fingerprints_by_year.csv"), index=False)
plog("  -> p2_fingerprints_by_year.csv")

# ── 2.6 Scopes by year ──────────────────────────────────────────
plog("2.6 Scopes by year ...")
scope_rows = []
for i, yc in enumerate(years_sorted):
    sub = master[master["year_cat"] == yc]
    scoped = sub[sub["scope"] != ""]
    n_sc = len(scoped)
    if n_sc == 0: continue
    sc_agg = scoped.groupby("scope").agg(
        pkgs=("name", "size"),
        pct1=("n_versions", lambda x: round(100*(x==1).sum()/len(x), 1)),
        dmin=("created_date", "min"),
        dmax=("created_date", "max"),
    ).nlargest(20, "pkgs")
    for sn, row in sc_agg.iterrows():
        fd, ld = row["dmin"], row["dmax"]
        try:
            wd = (ld - fd).days
        except Exception:
            wd = None
        scope_rows.append({"year": yc, "scope": sn, "packages": int(row["pkgs"]),
                           "pct_1ver": row["pct1"], "first": str(fd), "last": str(ld),
                           "window_days": wd})
    t20 = int(sc_agg["pkgs"].sum())
    t50 = int(scoped["scope"].value_counts().head(50).sum())
    scope_rows.append({"year": yc, "scope": "__TOP20_PCT__", "packages": t20,
                        "pct_1ver": round(100*t20/n_sc, 2), "first":"","last":"","window_days":None})
    scope_rows.append({"year": yc, "scope": "__TOP50_PCT__", "packages": t50,
                        "pct_1ver": round(100*t50/n_sc, 2), "first":"","last":"","window_days":None})
    if (i+1) % 5 == 0:
        plog(f"    scopes: {i+1}/{len(years_sorted)}")

pd.DataFrame(scope_rows).to_csv(os.path.join(OUT, "p2_scopes_by_year.csv"), index=False)
plog("  -> p2_scopes_by_year.csv")

# ── 2.6b Prefixes / suffixes (non-scoped) ───────────────────────
plog("2.6b Name prefixes/suffixes ...")
ns = master[~master["scoped"] & master["name"].notna()].copy()
parts_split = ns["name"].str.split("-")
ns["prefix"] = parts_split.str[0]
ns["suffix"] = parts_split.apply(lambda p: p[-1] if len(p) > 1 else "")

pfx_rows = []
for yc in years_sorted:
    sub = ns[ns["year_cat"] == yc]
    n = len(sub)
    if n == 0: continue
    for kind, col in [("prefix", "prefix"), ("suffix", "suffix")]:
        vc = sub[col].value_counts().head(20)
        for rank, (val, cnt) in enumerate(vc.items()):
            pfx_rows.append({"year": yc, "kind": kind, "rank": rank+1,
                             "term": val, "count": int(cnt), "pct": round(100*cnt/n, 2)})

pd.DataFrame(pfx_rows).to_csv(os.path.join(OUT, "p2_name_terms_by_year.csv"), index=False)
plog("  -> p2_name_terms_by_year.csv")
del ns, parts_split; gc.collect()

# ── 2.7 Top profile combos by year ──────────────────────────────
plog("2.7 Top profile combos by year ...")
combos_df = top_combos_by_year(master)
combos_df.to_csv(os.path.join(OUT, "p2_top_combos_by_year.csv"), index=False)
plog(f"  -> p2_top_combos_by_year.csv ({len(combos_df)} rows)")
fc_low_yrs = combos_df[combos_df["fc_low_coverage"]]["year"].unique()
if len(fc_low_yrs):
    plog(f"  file_count coverage < 0.9: {sorted(fc_low_yrs)}")

# ── 2.8 Emergent name families ──────────────────────────────────
plog("2.8 Emergent name families ...")
enf_df = emergent_name_families(master)
enf_df.to_csv(os.path.join(OUT, "p2_emergent_name_families.csv"), index=False)
n_fam = enf_df.groupby(["kind", "term", "year"]).ngroups if len(enf_df) else 0
plog(f"  -> p2_emergent_name_families.csv ({len(enf_df)} rows, {n_fam} distinct families)")

# ── 2.9 Group profiles and keywords ─────────────────────────────
plog("2.9 Group profiles and keywords ...")
gpk_df = group_profiles_and_keywords(master, enf_df, kw_cache)
gpk_df.to_csv(os.path.join(OUT, "p2_group_profiles_keywords.csv"), index=False)
plog(f"  -> p2_group_profiles_keywords.csv ({len(gpk_df)} rows)")

plog("PART 2 DONE.\n")

# ═══════════════════════════════════════════════════════════════════
#  PART 3: EXCLUSION INDICATORS
# ═══════════════════════════════════════════════════════════════════
plog("=" * 60)
plog("PART 3: EXCLUSION INDICATORS")
plog("=" * 60)

# ── 3.8 Indicators ──────────────────────────────────────────────
plog("3.8 Building indicators ...")

# spam_suspect
master["ind_spam"] = (master["dangling_share"] > 0.5) & (master["fan_out"] >= 10)
plog("  ind_spam done")

# scope_burst
plog("  scope_burst ...")
scoped_m = master[master["scope"] != ""]
sc_stats = scoped_m.groupby(["year_cat", "scope"]).agg(
    np=("name", "size"),
    p1=("n_versions", lambda x: 100*(x==1).sum()/len(x)),
    d0=("created_date", "min"),
    d1=("created_date", "max"),
).reset_index()
sc_stats["wd"] = sc_stats.apply(
    lambda r: (r["d1"] - r["d0"]).days if r["d0"] and r["d1"] and not pd.isna(r["d0"]) and not pd.isna(r["d1"]) else None,
    axis=1)

sb_params = [(50,90,95),(100,90,95),(50,90,100),(100,90,100),(200,365,95)]
for n_min, w_max, pv in sb_params:
    match = sc_stats[(sc_stats["np"]>=n_min) & sc_stats["wd"].notna() & (sc_stats["wd"]<=w_max) & (sc_stats["p1"]>=pv)]
    burst_set = set(zip(match["year_cat"], match["scope"]))
    col = f"ind_sb_{n_min}_{w_max}_{pv}"
    # vectorized: create temp key
    master["_sb_key"] = list(zip(master["year_cat"], master["scope"]))
    master[col] = master["_sb_key"].isin(burst_set) & (master["scope"] != "")
    master.drop(columns=["_sb_key"], inplace=True)
    plog(f"    {col}: {master[col].sum():,} flagged")

plog("  scope_burst done")

# ── 3.9 dep_group_burst ─────────────────────────────────────────
plog("3.9 dep_group_burst ...")
_hh = master[master["dep_list_hash"] != ""].copy()
_hh["_cd_ts"] = pd.to_datetime(_hh["created_date"])
_gs = _hh.groupby("dep_list_hash").agg(
    _sz=("name", "size"),
    _d0=("_cd_ts", "min"),
    _d1=("_cd_ts", "max"),
    _pv=("n_versions", lambda x: 100 * (x == 1).sum() / len(x)),
).reset_index()
_gs["_wd"] = (_gs["_d1"] - _gs["_d0"]).dt.days
_gi = _gs.set_index("dep_list_hash")
_m_sz = master["dep_list_hash"].map(_gi["_sz"])
_m_wd = master["dep_list_hash"].map(_gi["_wd"])
_m_pv = master["dep_list_hash"].map(_gi["_pv"])
DGB_T = [20, 100, 500]
DGB_W = [30, 90, 365]
DGB_P = [90, 95, 100]
for _t in DGB_T:
    for _w in DGB_W:
        for _p in DGB_P:
            col = f"ind_dgb_{_t}_{_w}_{_p}"
            master[col] = ((_m_sz >= _t) & _m_wd.notna()
                           & (_m_wd <= _w) & (_m_pv >= _p)).fillna(False)
            plog(f"    {col}: {master[col].sum():,}")
del _hh, _gs, _gi, _m_sz, _m_wd, _m_pv
plog("  dep_group_burst done")

# ── 3.10 emergent_name ──────────────────────────────────────────
plog("3.10 emergent_name ...")
if len(enf_df):
    _fam = enf_df.groupby(["kind", "term", "year"])["window_days"].min().reset_index()
else:
    _fam = pd.DataFrame(columns=["kind", "term", "year", "window_days"])
_sc2 = master["name"].str.startswith("@", na=False) & master["name"].str.contains("/", na=False)
_bare = master["name"].where(~_sc2, master["name"].str.split("/").str[1])
_pts = _bare.str.split("-")
_mpfx = _pts.str[0].fillna("")
_msfx = _pts.apply(lambda p: p[-1] if isinstance(p, list) and len(p) > 1 else "")
ENF_W = [30, 90, 365]
for _w in ENF_W:
    col = f"ind_enf_{_w}"
    _mask = pd.Series(False, index=master.index)
    _fw = _fam[_fam["window_days"].notna() & (_fam["window_days"] <= _w)]
    for _, _fr in _fw.iterrows():
        _tc = _mpfx if _fr["kind"] == "prefix" else _msfx
        _mask |= (master["year_cat"] == _fr["year"]) & (_tc == _fr["term"])
    master[col] = _mask
    plog(f"    {col}: {master[col].sum():,}")
del _fam, _sc2, _bare, _pts, _mpfx, _msfx
plog("  emergent_name done")

# ── 3.11 zero_maint ─────────────────────────────────────────────
master["ind_zero_maint"] = master["n_maintainers"] == 0
plog(f"  ind_zero_maint: {master['ind_zero_maint'].sum():,}")

# ── 3.12 types ──────────────────────────────────────────────────
master["ind_types"] = master["name"].str.startswith("@types/", na=False)
plog(f"  ind_types: {master['ind_types'].sum():,}")

# ── 3.13 platform_binary ────────────────────────────────────────
master["ind_platform_binary"] = master["name"].str.contains(PLATFORM_RE, na=False)
plog(f"  ind_platform_binary: {master['ind_platform_binary'].sum():,}")

# ── 3.13 Summary ────────────────────────────────────────────────
plog("3.13 Summary tables ...")
_cand_defs = [("ind_spam", True)]
for _sn, _sw, _sp in sb_params:
    _cand_defs.append((f"ind_sb_{_sn}_{_sw}_{_sp}", False))
for _t in DGB_T:
    for _w in DGB_W:
        for _p in DGB_P:
            _cand_defs.append((f"ind_dgb_{_t}_{_w}_{_p}", False))
for _w in ENF_W:
    _cand_defs.append((f"ind_enf_{_w}", False))
_cand_defs.append(("ind_zero_maint", False))
_cand_defs.append(("ind_types", False))
_cand_defs.append(("ind_platform_binary", False))

summary_df, counts_df = build_exclusion_summary(master, _cand_defs)
summary_df.to_csv(os.path.join(OUT, "p3_exclusion_candidates.csv"), index=False)
plog(f"  -> p3_exclusion_candidates.csv ({len(summary_df)} rows)")
counts_df.to_csv(os.path.join(OUT, "p3_candidate_counts_by_year.csv"), index=False)
plog(f"  -> p3_candidate_counts_by_year.csv ({len(counts_df)} rows)")

# ── Special cases ────────────────────────────────────────────────
plog("\nSpecial cases:")
pre = master[master["year_cat"] == "pre2010"]
plog(f"  pre-2010: {len(pre):,} pkgs, years={sorted(pre['created_year'].dropna().unique())}")
nd = master[master["year_cat"] == "no_date"]
plog(f"  no-date: {len(nd):,} pkgs")

plog("\n" + "=" * 60)
plog("ALL DONE")
plog("=" * 60)
