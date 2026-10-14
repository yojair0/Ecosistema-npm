#!/usr/bin/env python3
"""
Follow-up on the registry audit.

  1. Counts packages whose latest version is 0.0.1-security, the placeholder
     npm publishes after removing a malicious package, across the full
     profile, and shows their strata and eligibility.
  2. Lists sample names from the heaviest personal accounts.

Input : vm_results/**/profile/*.jsonl, results/strata_table.parquet,
        data/audit_sample.jsonl
"""
import glob
import json

import pandas as pd

ACCOUNTS = ["terryfei", "mipta19", "miptaa02", "mipppp",
            "mayangsario", "rajhsinggg", "bedlaj"]

rows = []
paths = (glob.glob("vm_results/data/profile/*.jsonl")
         + glob.glob("vm_results/part2/data/profile/*.jsonl"))
for path in paths:
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if d.get("latest") == "0.0.1-security":
                rows.append({"package": d["name"], "created": d.get("created")})

ph = pd.DataFrame(rows)
print(f"Latest version 0.0.1-security: {len(ph):,}")
if len(ph):
    ph["year"] = pd.to_datetime(ph["created"], utc=True, errors="coerce").dt.year
    print("\nBy creation year:")
    print(ph["year"].value_counts().sort_index().to_string())
    st = pd.read_parquet("results/strata_table.parquet",
                         columns=["package", "stratum_decade", "eligible"])
    m = ph.merge(st, on="package", how="left")
    print("\nBy stratum:")
    print(m.groupby("stratum_decade")
           .agg(packages=("package", "size"), eligible=("eligible", "sum"))
           .to_string())

a = pd.read_json("data/audit_sample.jsonl", lines=True)
print("\nPublished by 'npm':", ", ".join(a.loc[a["publisher"] == "npm", "name"].head(10)))
for acc in ACCOUNTS:
    names = a.loc[a["publisher"] == acc, "name"].head(8)
    print(f"\n{acc}: {', '.join(names)}")