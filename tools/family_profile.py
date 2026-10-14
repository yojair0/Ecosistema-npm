#!/usr/bin/env python3
"""
Automatic profile of every package family (scope).

Packages in one scope share an owner, often a template and code, so they are
not independent observations. Instead of labelling families by hand, each
one gets measurable features:

  packages          size of the family
  external_fan_in   dependents outside the scope: adoption by others
  internal_fan_in   dependents inside the scope: the family's own wiring
  one_version       share of packages with a single version
  burst             share created on the family's busiest day
  eligible          eligible packages under the current rules
  excluded_share    share already excluded

It also splits every package's fan-in into internal and external, and
reports how many packages would change stratum if strata used external
fan-in only.

Input : data/06_profile_analysis/profile_table.parquet,
        data/07_strata_analysis/strata_table.parquet,
        data/pasada2/*.jsonl
Output: data/07_strata_analysis/family_profile.csv,
        data/07_strata_analysis/fan_in_split.parquet
"""
import glob
import json
from collections import Counter

import numpy as np
import pandas as pd

MIN_FAMILY = 20
SNAPSHOT = pd.Timestamp("2026-09-18")
STRATA = ["0a isolated", "0b consumer", "1-9", "10-99", "100-999", ">=1000"]


def norm(name):
    return name.strip().lower()


def scope_of(name):
    return name.split("/")[0] if name.startswith("@") else ""


def decade(fi, fo):
    return np.select([(fi == 0) & (fo == 0), fi == 0, fi < 10, fi < 100,
                      fi < 1000], STRATA[:5], default=STRATA[5])


prof = pd.read_parquet("data/06_profile_analysis/profile_table.parquet",
                       columns=["package", "fan_in", "fan_out", "n_versions",
                                "age_days"])
st = pd.read_parquet("data/07_strata_analysis/strata_table.parquet",
                     columns=["package", "stratum_decade", "eligible",
                              "excluded"])
df = prof.merge(st, on="package")
nodes = set(df["package"])

print("Scanning dependency lists for intra-family edges...")
internal = Counter()
for path in sorted(glob.glob("data/pasada2/*.jsonl")):
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            deps = d.get("deps") or []
            if not deps:
                continue
            s = scope_of(norm(d["name"]))
            if not s:
                continue
            for x in deps:
                t = norm(x)
                if t in nodes and scope_of(t) == s:
                    internal[t] += 1

df["fan_in_internal"] = df["package"].map(internal).fillna(0).astype(int)
df["fan_in_external"] = df["fan_in"] - df["fan_in_internal"]
df["scope"] = df["package"].map(scope_of)
df["created_day"] = (SNAPSHOT - pd.to_timedelta(df["age_days"], unit="D")).dt.date
df["one_version"] = df["n_versions"] == 1

# ------------------------------------------------------- family profile
sc = df[df["scope"] != ""]
sizes = sc["scope"].value_counts()
sc = sc[sc["scope"].isin(sizes[sizes >= MIN_FAMILY].index)]
g = sc.groupby("scope")
fam = pd.DataFrame({
    "packages": g.size(),
    "external_fan_in": g["fan_in_external"].sum(),
    "internal_fan_in": g["fan_in_internal"].sum(),
    "max_external_fan_in": g["fan_in_external"].max(),
    "one_version": g["one_version"].mean().round(3),
    "eligible": g["eligible"].sum(),
    "excluded_share": g["excluded"].mean().round(3),
})
busiest = sc.groupby(["scope", "created_day"]).size().groupby(level=0).max()
fam["burst"] = (busiest / fam["packages"]).round(3)
fam = fam.sort_values("packages", ascending=False)
fam.to_csv("data/07_strata_analysis/family_profile.csv", encoding="utf-8-sig")

print(f"\nFamilies with {MIN_FAMILY}+ packages: {len(fam):,}, holding "
      f"{fam['packages'].sum():,} packages "
      f"({fam['packages'].sum() / len(df) * 100:.1f}% of the registry)")
print(f"... with no external fan-in at all: "
      f"{int((fam['external_fan_in'] == 0).sum()):,}")
print("\nLargest 15:")
print(fam.head(15).to_string())

# ------------------------------------------------- strata robustness
df["stratum_external"] = decade(df["fan_in_external"], df["fan_out"])
moved = df[df["stratum_external"] != df["stratum_decade"]]
print(f"\nPackages that change stratum with external fan-in only: {len(moved):,}")
print(pd.crosstab(moved["stratum_decade"], moved["stratum_external"]).to_string())

df[["package", "fan_in_internal", "fan_in_external", "stratum_external"]] \
    .to_parquet("data/07_strata_analysis/fan_in_split.parquet", index=False)
print("\nWrote data/07_strata_analysis/family_profile.csv and data/07_strata_analysis/fan_in_split.parquet")