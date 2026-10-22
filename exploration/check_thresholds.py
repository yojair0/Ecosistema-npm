#!/usr/bin/env python3
"""
Verification of the exclusion rules and their thresholds, over the full
population of the dependency network.

  1. Production dependencies declared, and how many point to names that do
     not exist.
  2. Missing dependencies: how many packages the spam-declarer rule can
     affect, how many it flags, how many sit just below its thresholds, and
     how the share of missing dependencies is distributed. If packages split
     into a group near 0% and a group near 100%, the 50% cut falls in an
     empty zone; if they spread evenly, the cut is arbitrary.
  3. Coordinated adoption: how often the pattern appears by creation period
     and number of dated dependents from other families, from 10 up.
     Packages created before 2020 predate the known spam campaigns, so their
     rate approximates how often organic packages meet it by chance.
  4. New rules by creation year, and the full list of coordinated cores
     created before 2021, where false positives would be.
  5. Share of each stratum flagged by the new rules.
  6. Coverage of the platform-binary rule on @rustbin.

Input : data/07_strata_analysis/signals.parquet
        data/06_profile_analysis/profile_table.parquet
Output: data/07_strata_analysis/cores_pre2021.csv
"""
import pandas as pd

OUT = "data/07_strata_analysis"
STRATA = ["0a isolated", "0b consumer", "1-9", "10-99", "100-999", ">=1000"]
cols = ["name", "stratum_raw", "fan_in_raw", "deps_declared", "deps_missing",
        "dangling_share", "dep_dated", "dep_span_p05_p95", "dep_recent_365",
        "platform_binary", "security_placeholder", "spam_declarer",
        "coordinated_core", "colluded_dependent", "excluded_any"]
s = pd.read_parquet(f"{OUT}/signals.parquet", columns=cols)
p = pd.read_parquet("data/06_profile_analysis/profile_table.parquet",
                    columns=["name", "created_year", "age_days"])
d = s.merge(p, on="name", how="left")
d["created_year"] = d["created_year"].astype(float)
n = len(d)


def line(label, k):
    print(f"  {label:<52}{k:>12,}  {k / n * 100:6.2f}%")


# ------------------------------------------------------------------ 1
print("1. Production dependencies\n")
declared, missing = int(d["deps_declared"].sum()), int(d["deps_missing"].sum())
print(f"  Declared:                   {declared:,}")
print(f"  To names that do not exist: {missing:,}")
print(f"  Between existing packages:  {declared - missing:,}")

# ------------------------------------------------------------------ 2
print("\n2. Missing dependencies (percentages over all packages)\n")
share = d["dangling_share"]
has_missing = d["deps_missing"] > 0
flagged = d["spam_declarer"]
line("All packages", n)
line("Declare at least one dependency", int((d["deps_declared"] > 0).sum()))
line("... and at least one does not exist", int(has_missing.sum()))
line("... flagged: 10+ declared, over 50% missing", int(flagged.sum()))
line("... not flagged", int((has_missing & ~flagged).sum()))
line("...... just below: 10+ declared, 30-50% missing",
     int(((d["deps_declared"] >= 10) & (share > 0.3) & (share <= 0.5)).sum()))
line("...... just below: 5-9 declared, over 50% missing",
     int((d["deps_declared"].between(5, 9) & (share > 0.5)).sum()))
m = d[has_missing]
rows = pd.cut(m["dangling_share"], [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0])
columns = pd.cut(m["deps_declared"], [0, 4, 9, 49, 10**6],
                 labels=["1-4 declared", "5-9", "10-49", "50+"])
print("\n  Share missing (rows) by dependencies declared (columns):\n")
print(pd.crosstab(rows, columns, margins=True).to_string())

# ------------------------------------------------------------------ 3
print("\n3. Coordinated-adoption pattern, from 10 dependents up\n")
c = d[d["dep_dated"] >= 10].copy()
c["flag"] = (c["dep_span_p05_p95"].between(0, 120)
             & (c["dep_recent_365"] / c["dep_dated"] <= 0.005)
             & (c["age_days"] >= 365))
c["dependents"] = pd.cut(c["dep_dated"], [9, 19, 49, 99, 10**7],
                         labels=["10-19", "20-49", "50-99", "100+"])
c["period"] = pd.cut(c["created_year"], [2010, 2019, 2023, 2024, 2026],
                     labels=["2011-2019", "2020-2023", "2024", "2025-2026"])
args = dict(index="period", columns="dependents", values="flag", observed=True)
print("  Percentage of packages that meet it:\n")
print(c.pivot_table(aggfunc="mean", **args).mul(100).round(1).to_string())
print("\n  Number of packages in each cell:\n")
print(c.pivot_table(aggfunc="size", **args).to_string())

# ------------------------------------------------------------------ 4
print("\n4. New rules by creation year\n")
g = d.dropna(subset=["created_year"]).groupby("created_year")
by_year = g[["coordinated_core", "colluded_dependent"]].sum().astype(int)
by_year.insert(0, "created", g.size())
by_year.index = by_year.index.astype(int)
print(by_year.to_string())
old = d[d["coordinated_core"] & (d["created_year"] < 2021)]
old = old.sort_values("fan_in_raw", ascending=False)
old[["name", "created_year", "fan_in_raw", "dep_dated", "dep_span_p05_p95"]] \
    .to_csv(f"{OUT}/cores_pre2021.csv", index=False)
print(f"\n  Coordinated cores created before 2021: {len(old):,} "
      f"(full list in {OUT}/cores_pre2021.csv)\n")
if len(old):
    print(old.head(25)[["name", "created_year", "fan_in_raw"]].to_string(index=False))

# ------------------------------------------------------------------ 5
print("\n5. Share of each stratum flagged\n")
rules = ["security_placeholder", "coordinated_core", "colluded_dependent", "excluded_any"]
t = d.groupby("stratum_raw")[rules].sum().reindex(STRATA)
t.insert(0, "total", d["stratum_raw"].value_counts().reindex(STRATA))
t["pct_excluded"] = (t["excluded_any"] / t["total"] * 100).round(1)
print(t.to_string())

# ------------------------------------------------------------------ 6
print("\n6. Platform binaries in @rustbin\n")
r = d[d["name"].str.startswith("@rustbin/")]
not_flagged = r[~r["platform_binary"]]
print(f"  @rustbin packages: {len(r):,} | not flagged: {len(not_flagged):,}")
if len(not_flagged):
    print(not_flagged["name"].head(15).to_string(index=False))