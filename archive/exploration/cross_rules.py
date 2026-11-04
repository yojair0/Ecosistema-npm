#!/usr/bin/env python3
"""
Cross-check between the network rules of pass 7b and the metadata
indicators of explore_exclusion_candidates.py, package by package.

The two methods look at different evidence: pass 7b at who depends on whom
and when those dependents were created; the indicators at bursts of
packages from one scope, identical dependency lists created within days,
and name families concentrated in one year. Agreement is evidence that a
rule captures a real pattern; disagreement points to what to inspect.

  1. Rules both scripts share: they should match, which checks the join.
  2. For each network rule, the share of its packages that the metadata
     indicators also flag, and the reverse.
  3. Coordinated cores born with their dependents, against older packages
     that received a burst of dependents later (possible victims).
  4. Disagreements, grouped by scope, written to CSV for inspection.

Input : data/07_strata_analysis/signals.parquet
        analysis_rerun/indicators.parquet
        data/06_profile_analysis/profile_table.parquet
Output: data/07_strata_analysis/cross_network_only.csv
        data/07_strata_analysis/cross_metadata_only.csv
"""
import os
import sys

import pandas as pd

SIGNALS = "data/07_strata_analysis/signals.parquet"
INDICATORS = "analysis_rerun/indicators.parquet"
PROFILE = "data/06_profile_analysis/profile_table.parquet"
OUT = "data/07_strata_analysis"
PERIODS = ["before 2024", "2024", "after 2024"]

if not os.path.exists(INDICATORS):
    sys.exit(f"Missing {INDICATORS}: run explore_exclusion_candidates.py with the save block first.")

net = pd.read_parquet(SIGNALS, columns=[
    "name", "stratum_raw", "fan_in_raw", "fan_in_clean", "dep_dated", "dep_within_120",
    "spam_declarer", "spam_propagated", "types_only", "platform_binary",
    "security_placeholder", "coordinated_core", "colluded_dependent", "excluded_any"])
ind = pd.read_parquet(INDICATORS)
prof = pd.read_parquet(PROFILE, columns=["name", "created_year"])
for df in (net, ind, prof):
    df["name"] = df["name"].astype(str).str.strip().str.lower()
d = (net.merge(ind.drop_duplicates("name"), on="name", how="left")
        .merge(prof.drop_duplicates("name"), on="name", how="left"))

ind_cols = [c for c in ind.columns if c.startswith("ind_")]
print(f"Packages: {len(d):,} | matched with indicators: {d['ind_spam'].notna().sum():,}")
d[ind_cols] = d[ind_cols].astype("boolean").fillna(False).astype(bool)
families = {"scope_burst": "ind_sb_", "identical_deps": "ind_dgb_", "name_family": "ind_enf_"}
for fam, prefix in families.items():
    d[fam] = d[[c for c in ind_cols if c.startswith(prefix)]].any(axis=1)
d["zero_maintainers"] = d["ind_zero_maint"]
d["metadata_any"] = d[list(families)].any(axis=1)
d["period"] = pd.cut(d["created_year"].astype(float), [0, 2023, 2024, 2100], labels=PERIODS)
new = d["coordinated_core"] | d["colluded_dependent"]


def pct(mask, col):
    return f"{d.loc[mask, col].mean() * 100:.1f}%" if mask.any() else "-"


# ------------------------------------------------------------------ 1
print("\n1. Rules both scripts share (should match)\n")
rows = []
for a, b in [("spam_declarer", "ind_spam"), ("types_only", "ind_types"),
             ("platform_binary", "ind_platform_binary")]:
    rows.append([a, int((d[a] & d[b]).sum()), int((d[a] & ~d[b]).sum()), int((~d[a] & d[b]).sum())])
print(pd.DataFrame(rows, columns=["rule", "both", "only 07b", "only Viki"]).to_string(index=False))

# ------------------------------------------------------------------ 2
print("\n2. Network rules: share also flagged by each metadata indicator\n")
fams = list(families) + ["zero_maintainers", "metadata_any"]
rows = [[r, int(d[r].sum())] + [pct(d[r], f) for f in fams]
        for r in ["coordinated_core", "colluded_dependent", "spam_declarer",
                  "spam_propagated", "security_placeholder"]]
print(pd.DataFrame(rows, columns=["07b rule", "packages"] + fams).to_string(index=False))

print("\n   Reverse: metadata indicators, share also flagged by 07b\n")
d["coordinated_or_colluded"] = new
rows = [[f, int(d[f].sum()), pct(d[f], "excluded_any"), pct(d[f], "coordinated_or_colluded")]
        for f in fams]
print(pd.DataFrame(rows, columns=["Viki indicator", "packages", "any 07b rule",
                                  "coordinated or colluded"]).to_string(index=False))

print("\n   Coordinated or colluded, by period and whether Viki's indicators agree\n")
t = pd.crosstab(d.loc[new, "period"], d.loc[new, "metadata_any"], margins=True)
print(t.rename(columns={False: "Viki: no", True: "Viki: yes"}).to_string())

# ------------------------------------------------------------------ 3
print("\n3. Coordinated cores: born with their dependents, or received them later?\n")
c = d[d["coordinated_core"]].copy()
c["born_with_package"] = c["dep_within_120"] / c["dep_dated"]
c["group"] = (c["created_year"] == 2024).map({True: "created 2024", False: "other years"})
print(c.groupby("group")["born_with_package"].describe().round(2).to_string())
old = c[c["created_year"] < 2021].sort_values("fan_in_raw", ascending=False)
print(f"\n   Cores created before 2021: {len(old):,}\n")
print(old[["name", "created_year", "fan_in_raw", "fan_in_clean", "born_with_package",
           "metadata_any"]].head(20).round(2).to_string(index=False))

# ------------------------------------------------------------------ 4
print("\n4. Disagreements, grouped by scope\n")
d["scope"] = d["name"].str.extract(r"^(@[^/]+)/", expand=False).fillna("(no scope)")
parts = [("Flagged by 07b (coordinated or colluded), not by Viki", d[new & ~d["metadata_any"]],
          "cross_network_only.csv"),
         ("Flagged by Viki, not by any 07b rule", d[d["metadata_any"] & ~d["excluded_any"]],
          "cross_metadata_only.csv")]
for label, part, path in parts:
    part[["name", "scope", "created_year", "stratum_raw", "fan_in_raw"]].to_csv(
        f"{OUT}/{path}", index=False)
    per = part["period"].value_counts().reindex(PERIODS)
    print(f"   {label}: {len(part):,} packages (list in {OUT}/{path})")
    print("   " + " | ".join(f"{k}: {v:,}" for k, v in per.items()))
    top = part.groupby("scope").agg(packages=("name", "size"), max_fan_in=("fan_in_raw", "max"))
    print(top.sort_values("packages", ascending=False).head(10).to_string())
    print()