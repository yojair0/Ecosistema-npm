#!/usr/bin/env python3
"""
Second follow-up on the registry audit.

  1. Latest version of the sampled packages whose latest release was
     published by the npm account, to find placeholder versions other than
     0.0.1-security.
  2. Census of the largest scopes, with eligible counts and an example
     name, to spot generated families.

Input : data/audit_sample.jsonl, vm_results/**/profile/*.jsonl,
        results/strata_table.parquet
"""
import glob
import json

import pandas as pd

a = pd.read_json("data/audit_sample.jsonl", lines=True)
npm_names = set(a.loc[a["publisher"] == "npm", "name"].str.strip().str.lower())

latest = {}
paths = (glob.glob("vm_results/data/profile/*.jsonl")
         + glob.glob("vm_results/part2/data/profile/*.jsonl"))
for path in paths:
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if d["name"] in npm_names:
                latest[d["name"]] = d.get("latest")

print(f"Sampled packages published by npm: {len(npm_names)}; "
      f"found in profile: {len(latest)}")
print("Their latest versions:")
print(pd.Series(latest).value_counts().head(10).to_string())

st = pd.read_parquet("results/strata_table.parquet",
                     columns=["package", "eligible"])
scoped = st[st["package"].str.startswith("@")].copy()
scoped["scope"] = scoped["package"].str.split("/").str[0]
g = scoped.groupby("scope").agg(packages=("package", "size"),
                                eligible=("eligible", "sum"),
                                example=("package", "first"))
print("\nLargest scopes:")
print(g.sort_values("packages", ascending=False).head(30).to_string())