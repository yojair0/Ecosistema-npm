#!/usr/bin/env python3
"""
Pass 6 -- Profile analysis against network position.

Joins the package profile (pass 04) with prod/dev fan-in and fan-out
(pass 03), derives fan-in for peer and optional dependencies, and writes
the report requested in the meeting notes:

  1.  coverage of the profile over the reference package list
  2.  descriptive statistics of every variable
  3.  Spearman correlation of each variable with fan-in and fan-out
       (full universe and fan-in > 0 subset)
  4.  redundant pairs (|rho| > 0.8)
  5.  age as a confounder: direct comparison >= 5 years vs < 1 year
  6.  the one-year eligibility window (fan-in and fan-out)
  7.  the fan-in / fan-out zero grid with profile coverage per quadrant
  8.  fan-in and fan-out by profile availability
  9.  fan-in and fan-out by binary groups
  10. deprecation rate by fan-in range
  11. median fan-in and fan-out by creation year
  12. median fan-in and fan-out by decile of n_versions, n_maintainers,
      n_keywords (mode group reported separately)
  13. outliers: packages before 2009 and monthly distribution of modified
  14. full Spearman correlation matrix

Works with whichever profile parts are present and flags partial coverage,
so it can be re-run unchanged once every part has been fetched.

Input : data/03_dependency_graph/graph_metrics.csv
        data/04_profile/part1/*.jsonl            (part 1)
        data/04_profile/part2/*.jsonl            (part 2, optional)
Output: data/06_profile_analysis/profile_report.md
        data/06_profile_analysis/profile_table.parquet
"""
import glob
import json
import os
import time
from collections import Counter

import numpy as np
import pandas as pd

GRAPH_CSV = "data/03_dependency_graph/graph_metrics.csv"
PARTS = {
    "part 1": "data/04_profile/part1",
    "part 2": "data/04_profile/part2",
}
OUT_DIR = "data/06_profile_analysis"
TABLES_DIR = os.path.join(OUT_DIR, "tables")
SNAPSHOT = pd.Timestamp("2026-09-18", tz="UTC")    # fan-in measured here
COLLECTION = pd.Timestamp("2026-10-10", tz="UTC")  # profile collected here
TOP_FAN_IN = 1000

FIELDS = ["n_peer", "n_opt", "n_maintainers", "deprecated", "n_keywords",
          "has_github", "file_count", "unpacked", "created", "modified",
          "n_versions"]

PARQUET_COLS = [
    "name",
    "fan_in", "fan_out",
    "fan_in_dev", "fan_out_dev",
    "fan_in_peer", "fan_in_opt",
    "fan_out_peer", "fan_out_opt",
    "n_versions", "n_maintainers", "n_keywords",
    "deprecated", "has_github", "scoped",
    "file_count", "unpacked",
    "age_days", "days_since_mod",
    "created_year", "has_profile",
]

T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.0f}s] {msg}", flush=True)


def save_table(df: pd.DataFrame, stem: str) -> None:
    os.makedirs(TABLES_DIR, exist_ok=True)
    path = os.path.join(TABLES_DIR, f"{stem}.csv")
    with open(path, "w", encoding="utf-8") as f:
        df.to_csv(f, index=False)


def write_run_metadata(meta: dict) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "run_metadata.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)


def load_graph():
    g = pd.read_csv(
        GRAPH_CSV,
        dtype={"paquete": str},
        keep_default_na=False,   # packages named "null" or "nan" exist
        na_values=[],
    )
    return g.rename(columns={"paquete": "package", "sin_version": "no_version"})


def load_profiles(nodes):
    """Reads every profile shard, keeping only what the analysis needs.

    Peer and optional fan-in are counted on the fly, so the edge lists are
    never held in memory. Only edges between two graph nodes are counted,
    consistent with how prod and dev fan-in were derived.
    """
    cols = {"package": []}
    cols.update({k: [] for k in FIELDS})
    fi_peer, fi_opt = Counter(), Counter()
    seen, found, dup = set(), [], 0

    for label, base in PARTS.items():
        files = sorted(glob.glob(f"{base}/*.jsonl"))
        if not files:
            continue
        found.append(label)
        log(f"reading {label}: {len(files)} shards")
        for path in files:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    d = json.loads(line)
                    name = d["name"]
                    if name in seen:
                        dup += 1
                        continue
                    seen.add(name)
                    cols["package"].append(name)
                    for k in FIELDS:
                        cols[k].append(d.get(k))
                    if name in nodes:
                        for dst in d.get("peer") or ():
                            if dst in nodes:
                                fi_peer[dst] += 1
                        for dst in d.get("opt") or ():
                            if dst in nodes:
                                fi_opt[dst] += 1
    return pd.DataFrame(cols), fi_peer, fi_opt, found, dup


def main():
    lines = []
    w = lines.append

    log("loading graph table")
    g = load_graph()
    nodes = set(g["package"])
    log(f"  {len(g):,} nodes")

    prof, fi_peer, fi_opt, found, dup = load_profiles(nodes)
    if not found:
        raise SystemExit("No profile shards found under data/04_profile/.")
    log(f"  {len(prof):,} profiles, {dup:,} duplicates skipped")

    g["fan_in_peer"] = g["package"].map(fi_peer).fillna(0).astype(int)
    g["fan_in_opt"] = g["package"].map(fi_opt).fillna(0).astype(int)

    log("joining and deriving variables")
    df = g.merge(prof, on="package", how="left", indicator=True)
    df["has_profile"] = df.pop("_merge") == "both"
    df = df.rename(columns={
        "n_peer": "fan_out_peer",
        "n_opt": "fan_out_opt",
        "package": "name",
    })

    created = pd.to_datetime(df["created"], utc=True, errors="coerce")
    modified = pd.to_datetime(df["modified"], utc=True, errors="coerce")
    df["age_days"] = (SNAPSHOT - created).dt.days
    df["days_since_mod"] = (COLLECTION - modified).dt.days
    mod_month = modified.dt.to_period("M")
    df.loc[df["age_days"] < 0, "age_days"] = np.nan
    df["created_year"] = created.dt.year
    df["scoped"] = df["name"].str.startswith("@").astype(int)
    for c in ("deprecated", "has_github"):
        df[c] = df[c].map({True: 1, False: 0})
    df = df.drop(columns=["created", "modified"])

    prof_df = df[df["has_profile"]]

    n = len(df)
    n_with = len(prof_df)
    n_without = n - n_with
    fi0 = df["fan_in"] == 0
    fo0 = df["fan_out"] == 0

    def cell(mask):
        k = int(mask.sum())
        return f"{k:,} ({k / n * 100:.1f}%)"

    meta = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
        "reference_dates": {
            "snapshot": str(SNAPSHOT.date()),
            "collection": str(COLLECTION.date()),
        },
        "thresholds": {
            "top_fan_in": TOP_FAN_IN,
        },
        "input_rows": {
            "graph_nodes": n,
            "with_profile": n_with,
            "without_profile": n_without,
        },
        "lib_versions": {},
    }

    top = df["fan_in"] >= TOP_FAN_IN
    top_n = int(top.sum())
    top_cov = int((top & df["has_profile"]).sum())

    # ---------------------------------------------------------- 1. coverage
    w("# Profile analysis report\n")
    w(f"Generated {time.strftime('%Y-%m-%d %H:%M')}. Fan-in measured at "
      f"{SNAPSHOT.date()}; profile collected around {COLLECTION.date()}.\n")
    w("## 1. Population and coverage\n")
    w("| | n | share |\n|---|---|---|")
    w(f"| Graph nodes | {n:,} | 100% |")
    w(f"| With profile | {n_with:,} | {n_with / n * 100:.2f}% |")
    w(f"| Without profile | {n_without:,} | {n_without / n * 100:.2f}% |\n")
    w(f"Packages with fan_in >= {TOP_FAN_IN:,}: {top_n:,} total, "
      f"{top_cov:,} ({top_cov / max(top_n, 1) * 100:.1f}%) with profile.\n")
    w("### Zero grid (all nodes)\n")
    w("| | fan-out = 0 | fan-out > 0 |\n|---|---|---|")
    w(f"| fan-in = 0 | {cell(fi0 & fo0)} | {cell(fi0 & ~fo0)} |")
    w(f"| fan-in > 0 | {cell(~fi0 & fo0)} | {cell(~fi0 & ~fo0)} |\n")

    # ------------------------------------------------------ 2. descriptives
    NUM = ["fan_in", "fan_out", "fan_in_dev", "fan_out_dev",
           "fan_in_peer", "fan_out_peer", "fan_in_opt", "fan_out_opt",
           "age_days", "days_since_mod", "n_versions", "n_maintainers",
           "n_keywords", "file_count", "unpacked"]
    BIN = ["deprecated", "has_github", "scoped"]

    w("## 2. Descriptive statistics (packages with profile)\n")
    w("Statistics use only the values present for each variable. "
      "`n_null` indicates how many are missing. "
      "`pct_zeros` is computed over `n_valid`.\n")
    n_total = len(prof_df)
    w("| variable | n_total | n_null | pct_null | n_valid | "
      "median | mean | p90 | p99 | max | pct_zeros |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    num_rows = []
    for c in NUM:
        n_null = int(prof_df[c].isna().sum())
        pct_null = n_null / n_total * 100
        n_valid = int(prof_df[c].notna().sum())
        median = prof_df[c].median()
        mean = prof_df[c].mean()
        p90 = prof_df[c].quantile(0.90)
        p99 = prof_df[c].quantile(0.99)
        vmax = prof_df[c].max()
        pct_zeros = (
            (prof_df[c] == 0).sum() / n_valid * 100 if n_valid else float("nan")
        )
        w(f"| {c} | {n_total:,} | {n_null:,} | {pct_null:.2f}% | {n_valid:,} | "
          f"{median:,.2f} | {mean:,.2f} | {p90:,.2f} | {p99:,.2f} | "
          f"{vmax:,.2f} | {pct_zeros:.2f}% |")
        num_rows.append({
            "variable": c,
            "n_total": n_total,
            "n_null": n_null,
            "pct_null": pct_null,
            "n_valid": n_valid,
            "median": median,
            "mean": mean,
            "p90": p90,
            "p99": p99,
            "max": vmax,
            "pct_zeros": pct_zeros,
        })
    w("")
    w("| variable | n_total | n_null | n_valid | n_true | pct_true |")
    w("|---|---|---|---|---|---|")
    bin_rows = []
    for c in BIN:
        n_null = int(prof_df[c].isna().sum())
        n_valid = int(prof_df[c].notna().sum())
        n_true = int((prof_df[c] == 1).sum())
        pct_true = n_true / n_valid * 100 if n_valid else float("nan")
        w(f"| {c} | {n_total:,} | {n_null:,} | {n_valid:,} | {n_true:,} | "
          f"{pct_true:.2f}% |")
        bin_rows.append({
            "variable": c,
            "n_total": n_total,
            "n_null": n_null,
            "n_valid": n_valid,
            "n_true": n_true,
            "pct_true": pct_true,
        })
    w("")
    save_table(pd.DataFrame(num_rows), "s02_descriptives_numeric")
    save_table(pd.DataFrame(bin_rows), "s02_descriptives_binary")

    # ---------------------------------------------------- 3. fan-in section
    log("computing Spearman correlations (a few minutes)")
    VARS = [c for c in NUM if c not in ("fan_in", "fan_out")] + BIN
    corr = prof_df[["fan_in", "fan_out"] + VARS].corr(method="spearman")
    prof_pos = prof_df[prof_df["fan_in"] > 0]
    corr_pos = prof_pos[["fan_in", "fan_out"] + VARS].corr(method="spearman")

    corr_out = corr.copy()
    corr_out.index.name = "variable"
    save_table(corr_out.reset_index(), "correlation_matrix")

    FI_BINS = [0, 1, 10, 100, 1000, np.inf]
    FI_LABELS = ["0", "1–9", "10–99", "100–999", "≥ 1000"]
    ZERO_HEAVY = [
        "fan_in_dev", "fan_in_peer", "fan_in_opt",
        "fan_out_peer", "fan_out_opt", "n_keywords",
    ]
    TRAMO3_NUM = [
        "fan_out", "fan_in_dev", "fan_out_dev",
        "fan_in_peer", "fan_out_peer", "fan_in_opt", "fan_out_opt",
        "age_days", "days_since_mod", "n_versions", "n_maintainers",
        "n_keywords", "file_count", "unpacked",
    ]
    TRAMO3_BIN = ["deprecated", "has_github", "scoped"]

    meta["thresholds"]["fan_in_bins"] = [str(b) for b in FI_BINS]
    meta["thresholds"]["fan_in_labels"] = FI_LABELS

    fi_cut = pd.cut(
        prof_df["fan_in"], bins=FI_BINS, labels=FI_LABELS, right=False,
    )

    w("## 3. Variables by fan-in\n")
    w("### 3a. Profile by fan-in range\n")
    hdr3a = ["tramo", "n"] + TRAMO3_NUM + TRAMO3_BIN
    w("| " + " | ".join(hdr3a) + " |")
    w("|" + "---|" * len(hdr3a))

    tramo3_rows = []
    n_check = 0
    for lbl in FI_LABELS:
        sub = prof_df[fi_cut == lbl]
        n_sub = len(sub)
        n_check += n_sub
        mark = lbl + (" (n pequeño)" if n_sub < 100 else "")
        row = {"tramo": lbl, "n": n_sub, "small_n": n_sub < 100}
        parts = [mark, f"{n_sub:,}"]
        for c in TRAMO3_NUM:
            v = sub[c].median()
            row[c] = v
            parts.append(f"{v:,.2f}" if pd.notna(v) else "—")
        for c in TRAMO3_BIN:
            n_b = int(sub[c].notna().sum())
            v = sub[c].sum() / n_b * 100 if n_b else float("nan")
            row[c] = v
            parts.append(f"{v:.2f}%" if pd.notna(v) else "—")
        tramo3_rows.append(row)
        w("| " + " | ".join(parts) + " |")

    if n_check != len(prof_df):
        log(f"WARNING: fan_in tramo sum {n_check:,} != prof_df {len(prof_df):,}")
    w(f"\nTotal across tramos: {n_check:,} (expected {len(prof_df):,}).\n")
    save_table(pd.DataFrame(tramo3_rows), "s03_fanin_by_tramo")

    w("### 3b. Share with value > 0 for zero-heavy variables\n")
    hdr3b = ["tramo", "n"] + [f"{c}_pct_pos" for c in ZERO_HEAVY]
    w("| " + " | ".join(hdr3b) + " |")
    w("|" + "---|" * len(hdr3b))

    zh3_rows = []
    for lbl in FI_LABELS:
        sub = prof_df[fi_cut == lbl]
        n_sub = len(sub)
        row = {"tramo": lbl, "n": n_sub}
        parts = [lbl, f"{n_sub:,}"]
        for c in ZERO_HEAVY:
            n_v = int(sub[c].notna().sum())
            pct = (sub[c] > 0).sum() / n_v * 100 if n_v else float("nan")
            row[f"{c}_pct_pos"] = pct
            parts.append(f"{pct:.2f}%" if pd.notna(pct) else "—")
        zh3_rows.append(row)
        w("| " + " | ".join(parts) + " |")
    w("")
    save_table(pd.DataFrame(zh3_rows), "s03_fanin_by_tramo_pct_pos")

    w("### 3c. Spearman with fan-in\n")
    fi_spearman_vars = ["fan_out"] + sorted(
        VARS, key=lambda v: abs(corr.loc[v, "fan_in"]), reverse=True,
    )
    spearman3_rows = []
    w("| variable | rho_all | n_all | rho_fan_in_pos | n_fan_in_pos |")
    w("|---|---|---|---|---|")
    for v in fi_spearman_vars:
        rho_all = corr.loc[v, "fan_in"]
        rho_pos = corr_pos.loc[v, "fan_in"]
        n_all_v = int(prof_df[v].notna().sum())
        n_pos_v = int(prof_pos[v].notna().sum())
        w(f"| {v} | {rho_all:+.3f} | {n_all_v:,} | {rho_pos:+.3f} | {n_pos_v:,} |")
        spearman3_rows.append({
            "variable": v,
            "rho_all": round(rho_all, 4),
            "n_all": n_all_v,
            "rho_fan_in_pos": round(rho_pos, 4),
            "n_fan_in_pos": n_pos_v,
        })
    w("")
    save_table(pd.DataFrame(spearman3_rows), "s03_spearman_fanin")

    # -------------------------------------------------- 4. fan-out section
    prof_fo_pos = prof_df[prof_df["fan_out"] > 0]
    corr_fo_pos = prof_fo_pos[["fan_in", "fan_out"] + VARS].corr(method="spearman")

    FO_BINS = [0, 1, 3, 10, 50, np.inf]
    FO_LABELS = ["0", "1–2", "3–9", "10–49", "≥ 50"]
    ZERO_HEAVY4 = ["fan_in"] + ZERO_HEAVY
    TRAMO4_NUM = [
        "fan_in", "fan_in_dev", "fan_out_dev",
        "fan_in_peer", "fan_out_peer", "fan_in_opt", "fan_out_opt",
        "age_days", "days_since_mod", "n_versions", "n_maintainers",
        "n_keywords", "file_count", "unpacked",
    ]
    TRAMO4_BIN = ["deprecated", "has_github", "scoped"]

    meta["thresholds"]["fan_out_bins"] = [str(b) for b in FO_BINS]
    meta["thresholds"]["fan_out_labels"] = FO_LABELS

    fo_cut = pd.cut(
        prof_df["fan_out"], bins=FO_BINS, labels=FO_LABELS, right=False,
    )

    w("## 4. Variables by fan-out\n")
    w("### 4a. Profile by fan-out range\n")
    hdr4a = ["tramo", "n"] + TRAMO4_NUM + TRAMO4_BIN
    w("| " + " | ".join(hdr4a) + " |")
    w("|" + "---|" * len(hdr4a))

    tramo4_rows = []
    n_check4 = 0
    for lbl in FO_LABELS:
        sub = prof_df[fo_cut == lbl]
        n_sub = len(sub)
        n_check4 += n_sub
        mark = lbl + (" (n pequeño)" if n_sub < 100 else "")
        row = {"tramo": lbl, "n": n_sub, "small_n": n_sub < 100}
        parts = [mark, f"{n_sub:,}"]
        for c in TRAMO4_NUM:
            v = sub[c].median()
            row[c] = v
            parts.append(f"{v:,.2f}" if pd.notna(v) else "—")
        for c in TRAMO4_BIN:
            n_b = int(sub[c].notna().sum())
            v = sub[c].sum() / n_b * 100 if n_b else float("nan")
            row[c] = v
            parts.append(f"{v:.2f}%" if pd.notna(v) else "—")
        tramo4_rows.append(row)
        w("| " + " | ".join(parts) + " |")

    if n_check4 != len(prof_df):
        log(f"WARNING: fan_out tramo sum {n_check4:,} != prof_df {len(prof_df):,}")
    w(f"\nTotal across tramos: {n_check4:,} (expected {len(prof_df):,}).\n")
    save_table(pd.DataFrame(tramo4_rows), "s04_fanout_by_tramo")

    w("### 4b. Share with value > 0 for zero-heavy variables\n")
    hdr4b = ["tramo", "n"] + [f"{c}_pct_pos" for c in ZERO_HEAVY4]
    w("| " + " | ".join(hdr4b) + " |")
    w("|" + "---|" * len(hdr4b))

    zh4_rows = []
    for lbl in FO_LABELS:
        sub = prof_df[fo_cut == lbl]
        n_sub = len(sub)
        row = {"tramo": lbl, "n": n_sub}
        parts = [lbl, f"{n_sub:,}"]
        for c in ZERO_HEAVY4:
            n_v = int(sub[c].notna().sum())
            pct = (sub[c] > 0).sum() / n_v * 100 if n_v else float("nan")
            row[f"{c}_pct_pos"] = pct
            parts.append(f"{pct:.2f}%" if pd.notna(pct) else "—")
        zh4_rows.append(row)
        w("| " + " | ".join(parts) + " |")
    w("")
    save_table(pd.DataFrame(zh4_rows), "s04_fanout_by_tramo_pct_pos")

    w("### 4c. Spearman with fan-out\n")
    fo_spearman_vars = ["fan_in"] + sorted(
        VARS, key=lambda v: abs(corr.loc[v, "fan_out"]), reverse=True,
    )
    spearman4_rows = []
    w("| variable | rho_all | n_all | rho_fan_out_pos | n_fan_out_pos |")
    w("|---|---|---|---|---|")
    for v in fo_spearman_vars:
        rho_all = corr.loc[v, "fan_out"]
        rho_pos = corr_fo_pos.loc[v, "fan_out"]
        n_all_v = int(prof_df[v].notna().sum())
        n_pos_v = int(prof_fo_pos[v].notna().sum())
        w(f"| {v} | {rho_all:+.3f} | {n_all_v:,} | {rho_pos:+.3f} | {n_pos_v:,} |")
        spearman4_rows.append({
            "variable": v,
            "rho_all": round(rho_all, 4),
            "n_all": n_all_v,
            "rho_fan_out_pos": round(rho_pos, 4),
            "n_fan_out_pos": n_pos_v,
        })
    w("")
    save_table(pd.DataFrame(spearman4_rows), "s04_spearman_fanout")

    # ----------------------------------------- 5. connected group Spearman
    w("## 5. Variables en el grupo con ambas conexiones (fan_in > 0 y fan_out > 0)\n")
    prof_both = prof_df[(prof_df["fan_in"] > 0) & (prof_df["fan_out"] > 0)]
    n_both = len(prof_both)
    w(f"Paquetes con fan_in > 0 **y** fan_out > 0: **{n_both:,}** "
      f"({n_both / len(prof_df) * 100:.1f}% del universo con perfil).\n")
    corr_both = prof_both[["fan_in", "fan_out"] + VARS].corr(method="spearman")
    r_fi_fo_both = corr_both.loc["fan_in", "fan_out"]
    sorted_vars5 = sorted(
        VARS,
        key=lambda v: max(abs(corr_both.loc[v, "fan_in"]), abs(corr_both.loc[v, "fan_out"])),
        reverse=True,
    )
    spearman5_rows = []
    for v in sorted_vars5:
        n_v = int(prof_both[v].notna().sum())
        spearman5_rows.append({
            "variable": v,
            "rho_fan_in": round(corr_both.loc[v, "fan_in"], 4),
            "rho_fan_out": round(corr_both.loc[v, "fan_out"], 4),
            "n": n_v,
        })
    spearman5_rows.append({
        "variable": "fan_in ~ fan_out",
        "rho_fan_in": round(r_fi_fo_both, 4),
        "rho_fan_out": round(r_fi_fo_both, 4),
        "n": n_both,
    })
    w("| variable | rho_fan_in | rho_fan_out | n |")
    w("|---|---|---|---|")
    for row in spearman5_rows:
        w(f"| {row['variable']} | {row['rho_fan_in']:+.4f} | "
          f"{row['rho_fan_out']:+.4f} | {row['n']:,} |")
    w("")
    save_table(pd.DataFrame(spearman5_rows), "s05_spearman_both")

    # ----------------------------------------------------- 6. edad y cohortes
    AGE_THRESHOLD = 365
    meta["thresholds"]["age_window"] = AGE_THRESHOLD

    def _grp_stats(grp: pd.DataFrame) -> dict:
        fi = grp["fan_in"]
        fo = grp["fan_out"]
        fi_pos = fi[fi > 0]
        n = len(grp)
        return {
            "n": n,
            "pct_fi_pos": round((fi > 0).mean() * 100, 2) if n else float("nan"),
            "median_fi_pos": float(fi_pos.median()) if len(fi_pos) else float("nan"),
            "median_fo": float(fo.median()) if n else float("nan"),
            "pct_fo_zero": round((fo == 0).mean() * 100, 2) if n else float("nan"),
            "pct_one_version": round((grp["n_versions"] == 1).mean() * 100, 2) if n else float("nan"),
            "pct_github": round(grp["has_github"].mean() * 100, 2) if n else float("nan"),
            "pct_scoped": round(grp["scoped"].mean() * 100, 2) if n else float("nan"),
        }

    # §6a — por año de creación
    w("## 6. Edad y cohortes\n")
    w("### 6a. Por año de creación\n")
    w("Paquetes con fecha de creación posterior al snapshot (2026-09-18) aparecen "
      "en el año 2026, no en 'sin fecha'.\n")
    year_rows = []
    n_check6 = 0
    for yr, grp in prof_df.groupby("created_year", dropna=False):
        stats = _grp_stats(grp)
        stats["year"] = "sin fecha" if pd.isna(yr) else int(yr)
        n_check6 += stats["n"]
        year_rows.append(stats)
    if n_check6 != len(prof_df):
        log(f"WARNING §6a: row count mismatch {n_check6} != {len(prof_df)}")
    year_df = pd.DataFrame(year_rows)[["year", "n", "pct_fi_pos", "median_fi_pos",
                                       "median_fo", "pct_fo_zero", "pct_one_version",
                                       "pct_github", "pct_scoped"]]
    w("| year | n | pct_fi_pos | median_fi_pos | median_fo | pct_fo_zero | "
      "pct_one_version | pct_github | pct_scoped |")
    w("|---|---|---|---|---|---|---|---|---|")
    for _, row in year_df.iterrows():
        w(f"| {row['year']} | {int(row['n']):,} | {row['pct_fi_pos']:.1f}% | "
          f"{row['median_fi_pos']:.1f} | {row['median_fo']:.1f} | "
          f"{row['pct_fo_zero']:.1f}% | {row['pct_one_version']:.1f}% | "
          f"{row['pct_github']:.1f}% | {row['pct_scoped']:.1f}% |")
    w("")
    save_table(year_df, "s06_by_year")

    # §6b — ventana de 365 días
    w("### 6b. Ventana de 365 días\n")
    age = prof_df["age_days"]
    age_groups = [
        ("≥ 365 días", prof_df[age >= AGE_THRESHOLD]),
        ("< 365 días", prof_df[age < AGE_THRESHOLD]),
        ("sin edad",   prof_df[age.isna()]),
    ]
    age_window_rows = []
    for lbl, grp in age_groups:
        stats = _grp_stats(grp)
        stats["group"] = lbl
        age_window_rows.append(stats)
    age_win_df = pd.DataFrame(age_window_rows)[["group", "n", "pct_fi_pos", "median_fi_pos",
                                                 "median_fo", "pct_fo_zero", "pct_one_version",
                                                 "pct_github", "pct_scoped"]]
    w("| group | n | pct_fi_pos | median_fi_pos | median_fo | pct_fo_zero | "
      "pct_one_version | pct_github | pct_scoped |")
    w("|---|---|---|---|---|---|---|---|---|")
    for _, row in age_win_df.iterrows():
        w(f"| {row['group']} | {int(row['n']):,} | {row['pct_fi_pos']:.1f}% | "
          f"{row['median_fi_pos']:.1f} | {row['median_fo']:.1f} | "
          f"{row['pct_fo_zero']:.1f}% | {row['pct_one_version']:.1f}% | "
          f"{row['pct_github']:.1f}% | {row['pct_scoped']:.1f}% |")
    w("")
    save_table(age_win_df, "s06_age_window")

    # ------------------------------------------------- 7. perfil por rangos
    log("computing §7 — profile by ranges")
    w("## 7. Perfil por rangos (deciles con grupo de moda aparte)\n")
    w("El grupo de la moda se separa antes de calcular los deciles. "
      "Cortes duplicados se descartan (`duplicates='drop'`). "
      "Para `n_maintainers` se separa además el grupo con valor 0.\n")

    for col in ("n_versions", "n_maintainers", "n_keywords"):
        valid = prof_df[prof_df[col].notna()]
        mode_val = int(valid[col].value_counts().idxmax())
        mode_grp = valid[valid[col] == mode_val]
        excl = valid[col] == mode_val
        if col == "n_maintainers" and mode_val != 0:
            zero_grp = valid[valid[col] == 0]
            excl = excl | (valid[col] == 0)
        else:
            zero_grp = None
        rest = valid[~excl].copy()

        w(f"### {col} (mode = {mode_val}, n_mode = {len(mode_grp):,})\n")
        w("| range | n | median_fan_in | pct_fi_pos | "
          "median_fan_in_pos | median_fan_out | pct_fo_zero |")
        w("|---|---|---|---|---|---|---|")

        table_rows = []
        special = (
            [("= 0", zero_grp), (f"mode = {mode_val}", mode_grp)]
            if zero_grp is not None and len(zero_grp) > 0
            else [(f"mode = {mode_val}", mode_grp)]
        )
        for lbl, grp in special:
            fi = grp["fan_in"]; fo = grp["fan_out"]
            fi_pos = fi[fi > 0]
            mfip = float(fi_pos.median()) if len(fi_pos) else float("nan")
            w(f"| {lbl} | {len(grp):,} | {fi.median():.0f} | "
              f"{(fi > 0).mean() * 100:.1f}% | {mfip:.0f} | "
              f"{fo.median():.0f} | {(fo == 0).mean() * 100:.1f}% |")
            table_rows.append({"range": lbl, "n": len(grp),
                                "median_fan_in": float(fi.median()),
                                "pct_fi_pos": round((fi > 0).mean() * 100, 2),
                                "median_fan_in_pos": mfip,
                                "median_fan_out": float(fo.median()),
                                "pct_fo_zero": round((fo == 0).mean() * 100, 2)})
        if len(rest) > 0:
            try:
                rest["_dec"] = pd.qcut(rest[col], q=10, duplicates="drop")
                for interval, grp in rest.groupby("_dec", observed=True):
                    fi = grp["fan_in"]; fo = grp["fan_out"]
                    fi_pos = fi[fi > 0]
                    mfip = float(fi_pos.median()) if len(fi_pos) else float("nan")
                    w(f"| {interval} | {len(grp):,} | {fi.median():.0f} | "
                      f"{(fi > 0).mean() * 100:.1f}% | {mfip:.0f} | "
                      f"{fo.median():.0f} | {(fo == 0).mean() * 100:.1f}% |")
                    table_rows.append({"range": str(interval), "n": len(grp),
                                       "median_fan_in": float(fi.median()),
                                       "pct_fi_pos": round((fi > 0).mean() * 100, 2),
                                       "median_fan_in_pos": mfip,
                                       "median_fan_out": float(fo.median()),
                                       "pct_fo_zero": round((fo == 0).mean() * 100, 2)})
            except ValueError as exc:
                w(f"| _(deciles no disponibles: {exc})_ | | | | | | |")
        w("")
        save_table(pd.DataFrame(table_rows), f"s07_{col}_by_decile")

    # ------------------------------------------ 8. grupos binarios
    log("computing §8 — binary groups")
    w("## 8. Variables binarias\n")
    w("| group | value | n | median_fan_in | pct_fi_pos | "
      "median_fan_in_pos | median_fan_out | pct_fo_zero |")
    w("|---|---|---|---|---|---|---|---|")

    bin8_rows = []
    bin_groups = [
        ("scoped",       prof_df["scoped"] == 1,      prof_df["scoped"] == 0),
        ("deprecated",   prof_df["deprecated"] == 1,  prof_df["deprecated"] == 0),
        ("has_github",   prof_df["has_github"] == 1,  prof_df["has_github"] == 0),
        ("has_keywords", prof_df["n_keywords"] > 0,   prof_df["n_keywords"] == 0),
    ]
    for bname, yes_mask, no_mask in bin_groups:
        for lbl, mask in [("yes", yes_mask), ("no", no_mask)]:
            sub = prof_df[mask]
            fi = sub["fan_in"]; fo = sub["fan_out"]
            fi_pos = fi[fi > 0]
            mfip = float(fi_pos.median()) if len(fi_pos) else float("nan")
            w(f"| {bname} | {lbl} | {len(sub):,} | {fi.median():.0f} | "
              f"{(fi > 0).mean() * 100:.1f}% | {mfip:.0f} | "
              f"{fo.median():.0f} | {(fo == 0).mean() * 100:.1f}% |")
            bin8_rows.append({"group": bname, "value": lbl, "n": len(sub),
                               "median_fan_in": float(fi.median()),
                               "pct_fi_pos": round((fi > 0).mean() * 100, 2),
                               "median_fan_in_pos": mfip,
                               "median_fan_out": float(fo.median()),
                               "pct_fo_zero": round((fo == 0).mean() * 100, 2)})
    w("")
    save_table(pd.DataFrame(bin8_rows), "s08_binary_groups")

    # ------------------------------------------------- 9. atípicos (descriptivo)
    log("computing §9 — outliers")
    w("## 9. Atípicos (solo descriptivo, no se eliminan paquetes)\n")

    n_after_snap = int(
        (prof_df["age_days"].isna() & prof_df["created_year"].notna()).sum()
    )
    anomalous = prof_df[prof_df["created_year"] < 2009]
    n_anomalous = len(anomalous)
    w(f"Paquetes con fecha de creación posterior al snapshot (2026-09-18): "
      f"**{n_after_snap:,}** (aparecen en el año 2026 de la tabla §6a; `age_days = NaN`).\n")
    w(f"Paquetes con año de creación anterior a 2009: **{n_anomalous:,}** "
      f"(npm se publicó en enero 2010; años anteriores son artefactos).\n")
    if n_anomalous > 0:
        min_yr = int(anomalous["created_year"].min())
        epoch_note = " (artefacto Unix epoch)" if min_yr == 1970 else ""
        w(f"Año mínimo encontrado: **{min_yr}**{epoch_note}.\n")
        yr_counts = anomalous["created_year"].value_counts().sort_index()
        w("| año | n |\n|---|---|")
        for yr, cnt in yr_counts.items():
            w(f"| {int(yr)} | {cnt:,} |")
    w("")

    w("### Conteo por encima del percentil 99.9\n")
    w("| variable | p99.9 | n_above |")
    w("|---|---|---|")
    p999_rows = []
    for c in NUM:
        col_data = prof_df[c].dropna()
        if len(col_data) == 0:
            continue
        thresh = col_data.quantile(0.999)
        n_above = int((col_data > thresh).sum())
        w(f"| {c} | {thresh:,.1f} | {n_above:,} |")
        p999_rows.append({"variable": c, "p999": thresh, "n_above": n_above})
    w("")
    save_table(pd.DataFrame(p999_rows), "s09_p999")

    w("### Top 10 por variable numérica\n")
    top10_rows = []
    for c in NUM:
        valid_c = prof_df[["name", c]].dropna(subset=[c])
        if len(valid_c) == 0:
            continue
        top10 = valid_c.nlargest(10, c)
        w(f"**{c}**\n")
        w(f"| name | {c} |")
        w("|---|---|")
        for _, row in top10.iterrows():
            w(f"| {row['name']} | {row[c]:,.0f} |")
            top10_rows.append({"variable": c, "name": row["name"], "value": row[c]})
        w("")
    save_table(pd.DataFrame(top10_rows), "s09_top10")

    w("### Distribución mensual de la fecha de última modificación\n")
    w("Abril y junio de 2022 muestran conteos anómalos por actualizaciones "
      "masivas de metadata no relacionadas con cambios reales. "
      "**`days_since_mod` no es un indicador fiable de recencia.**\n")
    mod_prof = mod_month.loc[prof_df.index].dropna()
    mod_counts = mod_prof.value_counts().sort_values(ascending=False)
    mod_df = pd.DataFrame({"month": mod_counts.index.astype(str),
                           "n": mod_counts.values})
    save_table(mod_df, "s09_modified_monthly")
    w("| month | n |\n|---|---|")
    for _, row in mod_df.head(20).iterrows():
        w(f"| {row['month']} | {int(row['n']):,} |")
    w("")

    # ---------------------------------------------------------- outputs
    os.makedirs(OUT_DIR, exist_ok=True)
    out_md = os.path.join(OUT_DIR, "profile_report.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log(f"wrote {out_md}")

    existing_cols = [c for c in PARQUET_COLS if c in df.columns]
    missing_cols = [c for c in PARQUET_COLS if c not in df.columns]
    for c in missing_cols:
        log(f"WARNING: column '{c}' not in df, skipped from parquet")
    out_parquet = os.path.join(OUT_DIR, "profile_table.parquet")
    df[existing_cols].to_parquet(out_parquet, index=False)
    log(f"wrote {out_parquet}")

    meta["lib_versions"] = {
        "pandas": pd.__version__,
        "numpy": np.__version__,
    }
    try:
        import pyarrow
        meta["lib_versions"]["pyarrow"] = pyarrow.__version__
    except ImportError:
        meta["lib_versions"]["pyarrow"] = "not installed"
    write_run_metadata(meta)
    log(f"wrote {os.path.join(OUT_DIR, 'run_metadata.json')}")


if __name__ == "__main__":
    main()