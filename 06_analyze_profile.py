#!/usr/bin/env python3
"""
Pass 6 -- Profile analysis against network position.

Joins the package profile (pass 04) with prod/dev fan-in and fan-out
(pass 03), derives fan-in for peer and optional dependencies, and writes
the report requested in the meeting notes:

  1. coverage of the profile over the reference package list
  2. descriptive statistics of every variable
  3. Spearman correlation of each variable with fan-in and fan-out
  4. redundant pairs (|rho| > 0.8)
  5. age as a confounder of fan-in
  6. the one-year eligibility window
  7. the fan-in / fan-out zero grid
  8. 1-D k-means strata on log(fan-in + 1) against Horgan's geometric
     boundaries, with profile coverage per stratum

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
from sklearn.cluster import KMeans

GRAPH_CSV = "data/metricas_externas.csv"
PARTS = {
    "part 1": "vm_results/data",
    "part 2": "vm_results/part2/data",
}
OUT_DIR = "results"
SNAPSHOT = pd.Timestamp("2026-09-18", tz="UTC")    # fan-in measured here
COLLECTION = pd.Timestamp("2026-10-10", tz="UTC")  # profile collected here
K_STRATA = 4
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
    neg_age = int((df["age_days"] < 0).sum())
    df.loc[df["age_days"] < 0, "age_days"] = np.nan
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
    w("Variables with moderate or high association help clusters follow "
      "network position; those near zero cut across it. Selecting variables "
      "by their association with the outcome must be reported as such.\n")
    w("| Variable | rho fan-in | rho fan-out | verdict |\n|---|---|---|---|")
    ranked = []
    for v in VARS:
        ri, ro = corr.loc[v, "fan_in"], corr.loc[v, "fan_out"]
        m = max(abs(ri), abs(ro))
        verdict = ("keep" if m >= .30 else
                   "borderline" if m >= .15 else "cuts across")
        ranked.append((m, v, ri, ro, verdict))
    for _, v, ri, ro, verdict in sorted(ranked, reverse=True):
        w(f"| {v} | {ri:+.3f} | {ro:+.3f} | {verdict} |")
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
    r_age = corr.loc["age_days", "fan_in"]
    w("## 5. Age as a confounder of fan-in\n")
    w(f"Spearman(age, fan-in) = **{r_age:+.3f}**.\n")
    if abs(r_age) >= .30:
        w("Fan-in accumulates with time. Age must enter the model as a "
          "control; otherwise the fan-in = 0 stratum mixes never-adopted "
          "packages with recently published ones.\n")
    elif abs(r_age) >= .15:
        w("Moderate association; controlling for age is advisable.\n")
    else:
        w("Weak association; age does not appear to confound fan-in.\n")

    # -------------------------------------------------- 6. one-year window
    w("## 6. One-year eligibility window\n")
    w("| Age at snapshot | packages | share | median fan-in | fan-in = 0 |")
    w("|---|---|---|---|---|")
    age = prof_df["age_days"]
    for lbl, m in [(">= 1 year", age >= 365), ("< 1 year", age < 365)]:
        s = prof_df.loc[m, "fan_in"]
        w(f"| {lbl} | {len(s):,} | {len(s) / len(prof_df) * 100:.1f}% | "
          f"{s.median():,.0f} | {(s == 0).mean() * 100:.1f}% |")
    w("")

    # ----------------------------------------------------- 7. zero grid
    w("## 7. Fan-in / fan-out zero grid (all nodes)\n")
    fi0, fo0 = df["fan_in"] == 0, df["fan_out"] == 0
    n = len(df)

    def cell(mask):
        k = int(mask.sum())
        return f"{k:,} ({k / n * 100:.1f}%)"

    w("| | fan-out = 0 | fan-out > 0 |\n|---|---|---|")
    w(f"| **fan-in = 0** | {cell(fi0 & fo0)} | {cell(fi0 & ~fo0)} |")
    w(f"| **fan-in > 0** | {cell(~fi0 & fo0)} | {cell(~fi0 & ~fo0)} |\n")

    # -------------------------------------------------------- 8. strata
    log("exploring strata")
    pos = df[df["fan_in"] > 0]
    x = np.log1p(pos["fan_in"].to_numpy()).reshape(-1, 1)

    w("## 8. Strata on log(fan-in + 1), fan-in > 0\n")
    w(f"{len(pos):,} packages. Fan-in = 0 is kept as its own stratum (0): as "
      f"a single point mass it cannot be clustered.\n")
    w("### Elbow\n\n| k | inertia |\n|---|---|")
    for k in range(2, 9):
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(x)
        w(f"| {k} | {km.inertia_:,.0f} |")
    w("")

    km = KMeans(n_clusters=K_STRATA, n_init=10, random_state=42).fit(x)
    order = np.argsort(km.cluster_centers_.ravel())
    rank = {c: i + 1 for i, c in enumerate(order)}
    df["stratum"] = 0
    df.loc[pos.index, "stratum"] = [rank[c] for c in km.labels_]

    w(f"### k-means (k={K_STRATA}) with profile coverage\n")
    w("| Stratum | fan-in range | packages | with profile | "
      ">= 1 year (of profiled) |\n|---|---|---|---|---|")
    for s in range(K_STRATA + 1):
        sub = df[df["stratum"] == s]
        if sub.empty:
            continue
        ps = sub[sub["has_profile"]]
        old = (ps["age_days"] >= 365).mean() * 100 if len(ps) else float("nan")
        w(f"| {s} | {sub['fan_in'].min():,} - {sub['fan_in'].max():,} | "
          f"{len(sub):,} | {sub['has_profile'].mean() * 100:.1f}% | "
          f"{old:.1f}% |")
    w("")

    fi = pos["fan_in"].to_numpy()
    lo_, hi_ = fi.min(), fi.max()
    r = (hi_ / lo_) ** (1 / K_STRATA)
    edges = [lo_] + [lo_ * r ** h for h in range(1, K_STRATA)] + [hi_ + 1]
    w(f"### Horgan geometric boundaries (L={K_STRATA})\n")
    w("| Stratum | fan-in range | packages |\n|---|---|---|")
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:]), 1):
        cnt = int(((fi >= lo) & (fi < hi)).sum())
        w(f"| {i} | {lo:,.0f} to <{hi:,.0f} | {cnt:,} |")
    w("\nIf both methods place their boundaries close together, the strata "
      "are supported by two independent criteria.\n")

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