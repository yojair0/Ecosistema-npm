#!/usr/bin/env python3
"""
Creation-cohort anomalies, on the full population.

Three views, all without sampling:

  1. packages created per month, with their share of packages with no
     dependencies, a single version, any dependent, and exclusions
  2. name words over-represented in 2024 compared with 2023
  3. coordinated fan-in: for every package with 50 or more dated
     dependents, the share of those dependents created within 30 days of
     the package itself. Organic adoption spreads over years; a network of
     packages published together that declare one another concentrates
     within days. Thresholds fixed in advance: 50 dependents, 30 days,
     80% of dependents.

Input : data/06_profile_analysis/profile_table.parquet
        data/07_strata_analysis/strata_table.parquet
        data/pasada2/*.jsonl
Output: data/07_strata_analysis/cohort_monthly.csv
        data/07_strata_analysis/coordinated_fan_in.csv
"""
import glob
import json
import re
from collections import Counter

import numpy as np
import pandas as pd

SNAPSHOT = pd.Timestamp("2026-09-18")
MIN_DEPENDENTS = 50
WINDOW_DAYS = 30
SHARE = 0.80
OUT = "data/07_strata_analysis"
REFERENCE = ["react", "lodash", "chalk", "cors", "ms", "ora", "strip-ansi"]


def norm(name):
    return name.strip().lower()


prof = pd.read_parquet("data/06_profile_analysis/profile_table.parquet",
                       columns=["name", "fan_in", "fan_out", "n_versions", "age_days"])
st = pd.read_parquet("data/07_strata_analysis/strata_table.parquet",
                     columns=["name", "excluded"])
df = prof.merge(st, on="name", how="left")
df["created"] = SNAPSHOT - pd.to_timedelta(df["age_days"], unit="D")
df["month"] = df["created"].dt.to_period("M")
df["no_deps"] = df["fan_out"] == 0
df["one_version"] = df["n_versions"] == 1
df["adopted"] = df["fan_in"] > 0
year = df["created"].dt.year

# ------------------------------------------------------ 1. per month
recent = df[df["month"] >= pd.Period("2021-01", "M")]
m = recent.groupby("month").agg(created=("name", "size"), no_deps=("no_deps", "mean"),
                                one_version=("one_version", "mean"),
                                adopted=("adopted", "mean"), excluded=("excluded", "mean"))
for c in ("no_deps", "one_version", "adopted", "excluded"):
    m[c] = (m[c].astype(float) * 100).round(1)
print("1. Packages created per month (shares in %)\n")
print(m.to_string())
m.to_csv(f"{OUT}/cohort_monthly.csv")

# ---------------------------------------------- 2. words in names
split = re.compile(r"[-_./@]+")


def words(names):
    c = Counter()
    for n in names:
        c.update({w for w in split.split(n) if len(w) >= 3 and not w.isdigit()})
    return c


n23, n24 = int((year == 2023).sum()), int((year == 2024).sum())
w23, w24 = words(df.loc[year == 2023, "name"]), words(df.loc[year == 2024, "name"])
rows = []
for w, c24 in w24.most_common():
    if c24 < 2000:
        break
    s24, s23 = c24 / n24, w23.get(w, 0) / n23
    rows.append((w, c24, round(s24 * 100, 2), round(s23 * 100, 2),
                 round(s24 / s23, 1) if s23 else np.inf))
ws = pd.DataFrame(rows, columns=["word", "packages_2024", "pct_2024", "pct_2023", "ratio"])
print("\n2. Words over-represented in 2024 names (2,000+ packages)\n")
print(ws.sort_values("ratio", ascending=False).head(20).to_string(index=False))

# ------------------------------------------- 3. coordinated fan-in
print("\n3. Scanning dependency lists (a few minutes)...")
dated = df[df["created"].notna()]
day = dict(zip(dated["name"],
               (dated["created"] - pd.Timestamp("1970-01-01")).dt.days.astype(int)))
total, close = Counter(), Counter()
for path in sorted(glob.glob("data/pasada2/*.jsonl")):
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            deps = d.get("deps") or []
            if not deps:
                continue
            s = day.get(norm(d["name"]))
            if s is None:
                continue
            for x in deps:
                target = norm(x)
                t = day.get(target)
                if t is None:
                    continue
                total[target] += 1
                if abs(s - t) <= WINDOW_DAYS:
                    close[target] += 1

df["dated_dependents"] = df["name"].map(total).fillna(0).astype(int)
df["close_dependents"] = df["name"].map(close).fillna(0).astype(int)
cand = df[df["dated_dependents"] >= MIN_DEPENDENTS].copy()
cand["close_share"] = (cand["close_dependents"] / cand["dated_dependents"]).round(3)
cand["coordinated"] = cand["close_share"] >= SHARE
cand["scoped"] = cand["name"].str.startswith("@")

print(f"\nPackages with {MIN_DEPENDENTS}+ dated dependents: {len(cand):,}")
print(f"... with coordinated fan-in: {int(cand['coordinated'].sum()):,}")
print("\nBy creation year:")
print(cand.groupby(cand["created"].dt.year)
          .agg(candidates=("name", "size"), coordinated=("coordinated", "sum"))
          .tail(10).to_string())
flag = cand[cand["coordinated"]].sort_values("fan_in", ascending=False)
cols = ["name", "fan_in", "close_share", "excluded", "scoped"]
print("\nTop 20 with coordinated fan-in:")
print(flag[cols].head(20).to_string(index=False))
print("\nKnown packages, for reference (must not be flagged):")
print(cand[cand["name"].isin(REFERENCE)][["name", "fan_in", "close_share", "coordinated"]]
      .to_string(index=False))
flag[["name", "fan_in", "dated_dependents", "close_share", "excluded", "scoped"]] \
    .to_csv(f"{OUT}/coordinated_fan_in.csv", index=False)