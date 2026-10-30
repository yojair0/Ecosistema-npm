#!/usr/bin/env python3
"""
Counts packages that declare themselves as a production dependency.

Pass 3 counts that declaration as one more dependent, so each of these
packages has a fan_in one higher than the number of other packages that use
it. It is also the only way a package in population B can have internal
fan-in, because in B every scope has a single package: the warning of
08_descriptive_stats.py should match the scoped packages counted here.

Input : data/pasada2/*.jsonl
        data/07_inclusion_packages/inclusion_flags.parquet
Output: data/07_inclusion_packages/post_check/self_dependencies.csv
"""
import glob
import json
from pathlib import Path

import pandas as pd

OUT = Path("data/07_inclusion_packages/post_check/self_dependencies.csv")

rows, seen = [], set()
for path in sorted(glob.glob("data/pasada2/*.jsonl")):
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if d.get("error") or not d.get("deps"):
                continue
            name = d["name"].strip().lower()
            if name in seen:
                continue
            seen.add(name)
            n_self = sum(1 for x in d["deps"] if x.strip().lower() == name)
            if n_self:
                rows.append({"name": name, "self_deps": n_self})

flags = pd.read_parquet("data/07_inclusion_packages/inclusion_flags.parquet",
                        columns=["name", "scope", "fan_in", "in_A", "in_B"])
m = flags.merge(pd.DataFrame(rows, columns=["name", "self_deps"]), on="name")
m["fan_in_without_self"] = m["fan_in"] - m["self_deps"]
OUT.parent.mkdir(parents=True, exist_ok=True)
m.sort_values("fan_in", ascending=False).to_csv(OUT, index=False)

scoped = m["scope"] != ""
a = m[m["in_A"]]
print(f"Packages that declare themselves: {len(m):,} "
      f"({int(scoped.sum()):,} scoped, {int((~scoped).sum()):,} unscoped)")
print(f"  in A: {len(a):,}; in B: {int(m['in_B'].sum()):,}")
print(f"  in B and scoped: {int((m['in_B'] & scoped).sum()):,} "
      f"(the warning of 08_descriptive_stats.py should be this number)")
print(f"  in A, fan-in only from themselves (fan_in would be 0): "
      f"{int((a['fan_in_without_self'] == 0).sum()):,}")
print(f"  in A, fan_in between 1 and 9 that would drop to 0: "
      f"{int(((a['fan_in'] <= 9) & (a['fan_in_without_self'] == 0)).sum()):,}")
neg = int((m["fan_in_without_self"] < 0).sum())
if neg:
    print(f"  NOTE: {neg:,} have a fan_in lower than their self-dependencies, so the "
          f"graph did not count the self-dependency for them")
print("\nTop 15 by fan_in:")
print(m.sort_values("fan_in", ascending=False).head(15)[
    ["name", "fan_in", "self_deps", "fan_in_without_self", "in_A", "in_B"]].to_string(index=False))
print(f"\nFull list: {OUT}")