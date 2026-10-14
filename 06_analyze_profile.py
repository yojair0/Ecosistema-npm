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

Input : data/metricas_externas.csv
        vm_results/data/profile/*.jsonl          (part 1)
        vm_results/part2/data/profile/*.jsonl    (part 2, optional)
Output: results/profile_report.md
        results/profile_table.parquet
"""
import glob
import json
import os
import time
from collections import Counter

import numpy as np
import pandas as pd

GRAPH_CSV = "data/metricas_externas.csv"
PARTS = {
    "part 1": "vm_results/data",
    "part 2": "vm_results/part2/data",
}
OUT_DIR = "results"
SNAPSHOT = pd.Timestamp("2026-09-18", tz="UTC")    # fan-in measured here
COLLECTION = pd.Timestamp("2026-10-10", tz="UTC")  # profile collected here
TOP_FAN_IN = 1000

FIELDS = ["n_peer", "n_opt", "n_maintainers", "deprecated", "n_keywords",
          "has_github", "file_count", "unpacked", "created", "modified",
          "n_versions"]

T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.0f}s] {msg}", flush=True)


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
        files = sorted(glob.glob(f"{base}/profile/*.jsonl"))
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


def load_run_counts():
    total = Counter()
    for base in PARTS.values():
        path = f"{base}/profile_run_meta.json"
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                total.update(json.load(f).get("counts", {}))
    return total


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    lines = []
    w = lines.append

    log("loading graph table")
    g = load_graph()
    nodes = set(g["package"])
    log(f"  {len(g):,} nodes")

    prof, fi_peer, fi_opt, found, dup = load_profiles(nodes)
    if not found:
        raise SystemExit("No profile shards found under vm_results/.")
    log(f"  {len(prof):,} profiles, {dup:,} duplicates skipped")

    g["fan_in_peer"] = g["package"].map(fi_peer).fillna(0).astype(int)
    g["fan_in_opt"] = g["package"].map(fi_opt).fillna(0).astype(int)

    log("joining and deriving variables")
    df = g.merge(prof, on="package", how="left", indicator=True)
    df["has_profile"] = df.pop("_merge") == "both"
    df = df.rename(columns={"n_peer": "fan_out_peer", "n_opt": "fan_out_opt"})

    created = pd.to_datetime(df["created"], utc=True, errors="coerce")
    modified = pd.to_datetime(df["modified"], utc=True, errors="coerce")
    df["age_days"] = (SNAPSHOT - created).dt.days
    df["days_since_mod"] = (COLLECTION - modified).dt.days
    mod_month = modified.dt.to_period("M")
    neg_age = int((df["age_days"] < 0).sum())
    df.loc[df["age_days"] < 0, "age_days"] = np.nan
    df["creation_year"] = created.dt.year
    df["scoped"] = df["package"].str.startswith("@").astype(int)
    for c in ("deprecated", "has_github"):
        df[c] = df[c].map({True: 1, False: 0})
    df = df.drop(columns=["created", "modified"])

    prof_df = df[df["has_profile"]]
    top = df["fan_in"] >= TOP_FAN_IN
    top_cov = int((top & df["has_profile"]).sum())

    # ---------------------------------------------------------- 1. coverage
    w("# Profile analysis report\n")
    w(f"Generated {time.strftime('%Y-%m-%d %H:%M')}. Fan-in measured at "
      f"{SNAPSHOT.date()}; profile collected around {COLLECTION.date()}.\n")
    w("## 1. Coverage\n")
    w("| | |\n|---|---|")
    w(f"| Graph nodes (reference list) | {len(df):,} |")
    w(f"| With profile | {len(prof_df):,} "
      f"({len(prof_df) / len(df) * 100:.2f}%) |")
    w(f"| Nodes with fan-in >= {TOP_FAN_IN:,} | {int(top.sum()):,} |")
    w(f"| ... of which with profile | {top_cov:,} "
      f"({top_cov / max(int(top.sum()), 1) * 100:.1f}%) |")
    w(f"| Profile parts found | {', '.join(found)} |\n")
    if len(found) < len(PARTS):
        w("> **Partial run.** Part 2 holds the packages updated after the "
          "reference snapshot, which are the most actively maintained. Until "
          "it is fetched, high fan-in packages are underrepresented and the "
          "correlations below are biased. Re-run once part 2 is in place.\n")

    counts = load_run_counts()
    if counts:
        w("### Extraction outcome\n\n| Status | Packages |\n|---|---|")
        for k, v in counts.most_common():
            w(f"| {k} | {v:,} |")
        w("")

    # ------------------------------------------------------ 2. descriptives
    NUM = ["fan_in", "fan_out", "fan_in_dev", "fan_out_dev",
           "fan_in_peer", "fan_out_peer", "fan_in_opt", "fan_out_opt",
           "age_days", "days_since_mod", "n_versions", "n_maintainers",
           "n_keywords", "file_count", "unpacked"]
    BIN = ["deprecated", "has_github", "scoped"]

    w("## 2. Descriptive statistics (packages with profile)\n")
    w("| Variable | n | median | mean | p90 | p99 | max | zeros |")
    w("|---|---|---|---|---|---|---|---|")
    for c in NUM:
        s = prof_df[c].dropna()
        if s.empty:
            continue
        w(f"| {c} | {len(s):,} | {s.median():,.0f} | {s.mean():,.1f} | "
          f"{s.quantile(.9):,.0f} | {s.quantile(.99):,.0f} | {s.max():,.0f} | "
          f"{(s == 0).mean() * 100:.1f}% |")
    w("\n| Binary | true | share |\n|---|---|---|")
    for c in BIN:
        s = prof_df[c].dropna()
        w(f"| {c} | {int(s.sum()):,} | {s.mean() * 100:.2f}% |")
    w("\nBinary variables are encoded 0/1; Spearman on ranks remains valid "
      "for them. Keywords enter as a count; the lists stay in the profile "
      "shards for interpreting clusters later.\n")
    if neg_age:
        w(f"_{neg_age:,} packages report a creation date after the snapshot "
          f"(re-created after unpublishing); their age is left empty._\n")

    # ---------------------------------------------------- 3. correlations
    log("computing Spearman correlations (a few minutes)")
    VARS = [c for c in NUM if c not in ("fan_in", "fan_out")] + BIN
    corr = prof_df[["fan_in", "fan_out"] + VARS].corr(method="spearman")

    w("## 3. Spearman correlation with fan-in and fan-out\n")
    w("### 3a. All packages with profile\n")
    w("| Variable | rho fan-in | rho fan-out |\n|---|---|---|")
    ranked = []
    for v in VARS:
        ri, ro = corr.loc[v, "fan_in"], corr.loc[v, "fan_out"]
        m = max(abs(ri), abs(ro))
        ranked.append((m, v, ri, ro))
    for _, v, ri, ro in sorted(ranked, reverse=True):
        w(f"| {v} | {ri:+.3f} | {ro:+.3f} |")
    w("")

    prof_pos = prof_df[prof_df["fan_in"] > 0]
    corr_pos = prof_pos[["fan_in", "fan_out"] + VARS].corr(method="spearman")
    w(f"### 3b. Packages with fan-in > 0 (n={len(prof_pos):,})\n")
    w("| Variable | rho fan-in | rho fan-out |\n|---|---|---|")
    ranked_pos = []
    for v in VARS:
        ri, ro = corr_pos.loc[v, "fan_in"], corr_pos.loc[v, "fan_out"]
        m = max(abs(ri), abs(ro))
        ranked_pos.append((m, v, ri, ro))
    for _, v, ri, ro in sorted(ranked_pos, reverse=True):
        w(f"| {v} | {ri:+.3f} | {ro:+.3f} |")
    w("")

    # ------------------------------------------------------ 4. redundancy
    w("## 4. Redundant pairs (|rho| > 0.8)\n")
    full = ["fan_in", "fan_out"] + VARS
    pairs = [(abs(corr.loc[a, b]), a, b, corr.loc[a, b])
             for i, a in enumerate(full) for b in full[i + 1:]
             if abs(corr.loc[a, b]) > .8]
    if pairs:
        w("| A | B | rho |\n|---|---|---|")
        for _, a, b, r in sorted(pairs, reverse=True):
            w(f"| {a} | {b} | {r:+.3f} |")
    else:
        w("None.")
    w("")

    # ------------------------------------------------------ 5. confounder
    r_age_fi = corr.loc["age_days", "fan_in"]
    r_age_fo = corr.loc["age_days", "fan_out"]
    w("## 5. Age as a confounder of fan-in and fan-out\n")
    w(f"Spearman(age, fan-in) = **{r_age_fi:+.3f}**. "
      f"Spearman(age, fan-out) = **{r_age_fo:+.3f}**.\n")
    w("The Spearman coefficient is suppressed by the zero mass (>83% of "
      "packages have fan-in = 0). The table below compares adoption rates "
      "directly across age groups.\n")
    age_fi = prof_df["age_days"].dropna()
    old_mask = age_fi >= 5 * 365
    new_mask = age_fi < 365
    pct_old = (prof_df.loc[old_mask.index[old_mask], "fan_in"] > 0).mean() * 100
    pct_new = (prof_df.loc[new_mask.index[new_mask], "fan_in"] > 0).mean() * 100
    w("| Age group | n | % with fan-in > 0 |\n|---|---|---|")
    w(f"| >= 5 years | {int(old_mask.sum()):,} | {pct_old:.1f}% |")
    w(f"| < 1 year | {int(new_mask.sum()):,} | {pct_new:.1f}% |")
    w("")

    # -------------------------------------------------- 6. one-year window
    w("## 6. One-year eligibility window\n")
    w("| Age at snapshot | packages | share | median fan-in | fan-in = 0 | "
      "median fan-out | fan-out = 0 |")
    w("|---|---|---|---|---|---|---|")
    age = prof_df["age_days"]
    for lbl, m in [(">= 1 year", age >= 365), ("< 1 year", age < 365)]:
        fi = prof_df.loc[m, "fan_in"]
        fo = prof_df.loc[m, "fan_out"]
        w(f"| {lbl} | {len(fi):,} | {len(fi) / len(prof_df) * 100:.1f}% | "
          f"{fi.median():,.0f} | {(fi == 0).mean() * 100:.1f}% | "
          f"{fo.median():,.0f} | {(fo == 0).mean() * 100:.1f}% |")
    w("")

    # ----------------------------------------------------- 7. zero grid
    w("## 7. Fan-in / fan-out zero grid (all nodes)\n")
    fi0, fo0 = df["fan_in"] == 0, df["fan_out"] == 0
    n = len(df)

    def cell(mask):
        k = int(mask.sum())
        cov = df.loc[mask, "has_profile"].mean() * 100 if k else 0.0
        return f"{k:,} ({k / n * 100:.1f}%) — {cov:.1f}% with profile"

    w("| | fan-out = 0 | fan-out > 0 |\n|---|---|---|")
    w(f"| **fan-in = 0** | {cell(fi0 & fo0)} | {cell(fi0 & ~fo0)} |")
    w(f"| **fan-in > 0** | {cell(~fi0 & fo0)} | {cell(~fi0 & ~fo0)} |\n")

    # ----------------------------------------- 8. with / without profile
    log("computing group comparisons")
    w("## 8. Fan-in and fan-out by profile availability (all nodes)\n")
    w("| has_profile | n | median fan-in | % fan-in > 0 | "
      "median fan-in (>0) | median fan-out | % fan-out = 0 |")
    w("|---|---|---|---|---|---|---|")
    for val, label in [(True, "yes"), (False, "no")]:
        sub = df[df["has_profile"] == val]
        fi = sub["fan_in"]
        fo = sub["fan_out"]
        fi_pos = fi[fi > 0]
        med_fi_pos = fi_pos.median() if len(fi_pos) else float("nan")
        w(f"| {label} | {len(sub):,} | {fi.median():,.0f} | "
          f"{(fi > 0).mean() * 100:.1f}% | {med_fi_pos:,.0f} | "
          f"{fo.median():,.0f} | {(fo == 0).mean() * 100:.1f}% |")
    w("")

    # ----------------------------------------- 9. binary group comparisons
    w("## 9. Fan-in and fan-out by binary groups (packages with profile)\n")
    w("| Group | value | n | median fan-in | % fan-in > 0 | "
      "median fan-in (>0) | median fan-out | % fan-out = 0 |")
    w("|---|---|---|---|---|---|---|---|")
    for col in ("scoped", "deprecated", "has_github"):
        for val, label in [(1, "yes"), (0, "no")]:
            sub = prof_df[prof_df[col] == val]
            fi = sub["fan_in"]
            fo = sub["fan_out"]
            fi_pos = fi[fi > 0]
            med_fi_pos = fi_pos.median() if len(fi_pos) else float("nan")
            w(f"| {col} | {label} | {len(sub):,} | {fi.median():,.0f} | "
              f"{(fi > 0).mean() * 100:.1f}% | {med_fi_pos:,.0f} | "
              f"{fo.median():,.0f} | {(fo == 0).mean() * 100:.1f}% |")
    has_kw = prof_df["n_keywords"] > 0
    for val, label in [(True, "yes"), (False, "no")]:
        sub = prof_df[has_kw == val]
        fi = sub["fan_in"]
        fo = sub["fan_out"]
        fi_pos = fi[fi > 0]
        med_fi_pos = fi_pos.median() if len(fi_pos) else float("nan")
        w(f"| has_keywords | {label} | {len(sub):,} | {fi.median():,.0f} | "
          f"{(fi > 0).mean() * 100:.1f}% | {med_fi_pos:,.0f} | "
          f"{fo.median():,.0f} | {(fo == 0).mean() * 100:.1f}% |")
    w("")

    # --------------------------------------- 10. deprecation rate by fan_in
    w("## 10. Deprecation rate by fan-in range (packages with profile)\n")
    fi_bins = [0, 1, 10, 100, 1000, 10000, np.inf]
    fi_labels = ["0", "1–9", "10–99", "100–999", "1000–9999", "≥ 10000"]
    fi_range = pd.cut(
        prof_df["fan_in"], bins=fi_bins, labels=fi_labels, right=False,
    )
    w("| fan-in range | n | deprecation rate |")
    w("|---|---|---|")
    for lbl in fi_labels:
        sub = prof_df[fi_range == lbl]
        rate = sub["deprecated"].mean() * 100 if len(sub) else float("nan")
        w(f"| {lbl} | {len(sub):,} | {rate:.2f}% |")
    w("")

    # --------------------------------------- 11. median by creation year
    w("## 11. Median fan-in and fan-out by creation year (packages with profile)\n")
    w("| year | n | median fan-in | % fan-in > 0 | "
      "median fan-in (>0) | median fan-out | % fan-out = 0 |")
    w("|---|---|---|---|---|---|---|")
    for yr, grp in prof_df.groupby("creation_year"):
        fi = grp["fan_in"]
        fo = grp["fan_out"]
        fi_pos = fi[fi > 0]
        med_fi_pos = fi_pos.median() if len(fi_pos) else float("nan")
        w(f"| {int(yr)} | {len(grp):,} | {fi.median():,.0f} | "
          f"{(fi > 0).mean() * 100:.1f}% | {med_fi_pos:,.0f} | "
          f"{fo.median():,.0f} | {(fo == 0).mean() * 100:.1f}% |")
    w("")

    # ------------------------------------------ 12. deciles with mode apart
    w("## 12. Median fan-in and fan-out by decile (packages with profile)\n")
    w("Mode group is reported separately; deciles are computed on the rest. "
      "Duplicate cut points are dropped.\n")
    for col in ("n_versions", "n_maintainers", "n_keywords"):
        valid = prof_df[prof_df[col].notna()]
        mode_val = valid[col].value_counts().idxmax()
        mode_grp = valid[valid[col] == mode_val]
        rest = valid[valid[col] != mode_val].copy()
        fi_m = mode_grp["fan_in"]
        fo_m = mode_grp["fan_out"]
        fi_m_pos = fi_m[fi_m > 0]
        med_fi_m_pos = fi_m_pos.median() if len(fi_m_pos) else float("nan")
        w(f"### {col} (mode = {mode_val}, n = {len(mode_grp):,})\n")
        w(f"| range | n | median fan-in | % fan-in > 0 | "
          f"median fan-in (>0) | median fan-out | % fan-out = 0 |")
        w("|---|---|---|---|---|---|---|")
        w(f"| mode={mode_val} | {len(mode_grp):,} | {fi_m.median():,.0f} | "
          f"{(fi_m > 0).mean() * 100:.1f}% | {med_fi_m_pos:,.0f} | "
          f"{fo_m.median():,.0f} | {(fo_m == 0).mean() * 100:.1f}% |")
        if len(rest) > 0:
            try:
                rest["_decile"] = pd.qcut(rest[col], q=10, duplicates="drop")
                for interval, grp in rest.groupby("_decile", observed=True):
                    fi = grp["fan_in"]
                    fo = grp["fan_out"]
                    fi_pos = fi[fi > 0]
                    med_fi_pos = fi_pos.median() if len(fi_pos) else float("nan")
                    w(f"| {interval} | {len(grp):,} | {fi.median():,.0f} | "
                      f"{(fi > 0).mean() * 100:.1f}% | {med_fi_pos:,.0f} | "
                      f"{fo.median():,.0f} | {(fo == 0).mean() * 100:.1f}% |")
            except ValueError as exc:
                w(f"| _(deciles unavailable: {exc})_ | | | | | | |")
        w("")

    # ----------------------------------------------- 13. outliers
    w("## 13. Outliers (descriptive only, no packages removed)\n")

    old_pkg = prof_df[prof_df["creation_year"] < 2009]
    w("### Packages with creation date before 2009\n")
    min_yr = int(old_pkg["creation_year"].min()) if len(old_pkg) > 0 else None
    epoch_note = (
        f" Earliest year found: {min_yr}"
        + (" (Unix epoch artefact)" if min_yr == 1970 else "") + "."
    ) if min_yr else ""
    w(f"{len(old_pkg):,} packages in the profile have a creation year before "
      f"2009.{epoch_note}\n")
    if len(old_pkg) > 0:
        yr_counts = old_pkg["creation_year"].value_counts().sort_index()
        w("| year | n |\n|---|---|")
        for yr, cnt in yr_counts.items():
            w(f"| {int(yr)} | {cnt:,} |")
    w("")

    mod_prof = mod_month.loc[prof_df.index].dropna()
    mod_counts = mod_prof.value_counts().sort_values(ascending=False)
    w("### Monthly distribution of last-modified date "
      "(packages with profile, top 20 by count)\n")
    w("April to June 2022 are expected to show anomalous counts due to "
      "mass metadata updates unrelated to actual package changes.\n")
    w("**days_since_mod is not a reliable recency indicator** because of "
      "these bulk updates; interpret it with caution throughout the "
      "report.\n")
    w("| month | n |\n|---|---|")
    for period, cnt in mod_counts.head(20).items():
        w(f"| {period} | {cnt:,} |")
    w("")

    # ------------------------------------------ 14. full correlation matrix
    CORR_ALL = [
        "fan_in", "fan_out", "fan_in_dev", "fan_out_dev",
        "fan_in_peer", "fan_in_opt",
        "fan_out_peer", "fan_out_opt",
        "age_days", "days_since_mod",
        "n_versions", "n_maintainers", "n_keywords",
        "file_count", "unpacked",
        "deprecated", "has_github", "scoped",
    ]
    corr_all = corr.loc[CORR_ALL, CORR_ALL]
    w("## 14. Full Spearman correlation matrix (packages with profile)\n")
    w("_days_since_mod is not reliable: mass metadata updates from April to "
      "June 2022 concentrate the distribution artificially._\n")
    w("| |" + "".join(f" {c} |" for c in CORR_ALL))
    w("|---|" + "".join("---|" for _ in CORR_ALL))
    for row in CORR_ALL:
        cells = "".join(f" {corr_all.loc[row, c]:+.2f} |" for c in CORR_ALL)
        w(f"| {row} |{cells}")
    w("")

    # ---------------------------------------------------------- outputs
    out_md = f"{OUT_DIR}/profile_report.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log(f"wrote {out_md}")

    try:
        df.to_parquet(f"{OUT_DIR}/profile_table.parquet", index=False)
        log(f"wrote {OUT_DIR}/profile_table.parquet")
    except ImportError:
        df.to_csv(f"{OUT_DIR}/profile_table.csv.gz", index=False,
                  compression="gzip")
        log(f"wrote {OUT_DIR}/profile_table.csv.gz")


if __name__ == "__main__":
    main()