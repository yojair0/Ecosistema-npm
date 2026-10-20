#!/usr/bin/env python3
"""
Two follow-up checks on the cohort anomalies, on the full population.

  A. For the packages with about 13,000 dependents and generated-looking
     names, how close in time their dependents were created: within 30
     days, 90 days and one year of the package itself.
  B. Packages whose latest version starts with 0.0.1-security, the
     placeholder npm leaves after removing a package: across the whole
     profile, and among the packages created in November 2025.

Input : data/06_profile_analysis/profile_table.parquet
        data/04_profile/part*/*.jsonl
        data/pasada2/*.jsonl
"""
import glob
import json

import pandas as pd

SNAPSHOT = pd.Timestamp("2026-09-18")
TARGETS = {"web3-eve-cli", "react-random-number-generator", "round-number-cli",
           "btuyen-btn-events", "number-extrarandom-cli", "pubteahy",
           "remove-value-js"}


def norm(name):
    return name.strip().lower()


# ---------------------------------------------------------------- A
prof = pd.read_parquet("data/06_profile_analysis/profile_table.parquet",
                       columns=["name", "age_days"])
prof = prof[prof["age_days"].notna()]
created = dict(zip(prof["name"],
                   SNAPSHOT - pd.to_timedelta(prof["age_days"], unit="D")))
dependents = {t: [] for t in TARGETS}
for path in glob.glob("data/pasada2/*.jsonl"):
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            for x in d.get("deps") or []:
                x = norm(x)
                if x in TARGETS:
                    c = created.get(norm(d["name"]))
                    if c is not None:
                        dependents[x].append(c)

print("A. Dependents of the ~13,000 group, by distance in time to the package\n")
for t in sorted(TARGETS):
    c = created.get(t)
    s = pd.Series(dependents[t])
    if c is None or s.empty:
        print(f"{t}: not enough data")
        continue
    gap = (s - c).dt.days.abs()
    print(f"{t}: created {c.date()} | {len(s):,} dated dependents | "
          f"30 days {(gap <= 30).mean() * 100:.0f}% | "
          f"90 days {(gap <= 90).mean() * 100:.0f}% | "
          f"1 year {(gap <= 365).mean() * 100:.0f}% | "
          f"from {s.min().date()} to {s.max().date()}")

# ---------------------------------------------------------------- B
total = exact = nov = nov_placeholder = 0
for path in glob.glob("data/04_profile/part*/*.jsonl"):
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            version = d.get("latest") or ""
            placeholder = version.startswith("0.0.1-security")
            total += placeholder
            exact += version == "0.0.1-security"
            if (d.get("created") or "").startswith("2025-11"):
                nov += 1
                nov_placeholder += placeholder

print(f"\nB. Latest version starting with 0.0.1-security: {total:,} "
      f"(exactly 0.0.1-security: {exact:,})")
print(f"   Created in November 2025: {nov:,}, of which placeholders: "
      f"{nov_placeholder:,} ({nov_placeholder / max(nov, 1) * 100:.1f}%)")