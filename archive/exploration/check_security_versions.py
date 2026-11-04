#!/usr/bin/env python3
"""
Checks the packages kept in population A whose version mentions "security":
whether npm's holding text or its account confirms them as placeholders.

The confirmed names are added to resources/npm_placeholders_confirmed.txt,
which 07b_inclusion_population.py reads to exclude them. The list only grows:
once 07b excludes those packages they no longer appear in population A, and
running this check again must not drop them from the list.

Output: data/07_inclusion_packages/post_check/security_versions_in_A.csv
        resources/npm_placeholders_confirmed.txt
"""
import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

POPULATION = "data/07_inclusion_packages/population_with_families.parquet"
OUT_CSV = Path("data/07_inclusion_packages/post_check/security_versions_in_A.csv")
CONFIRMED = Path("resources/npm_placeholders_confirmed.txt")

pop = pd.read_parquet(POPULATION, columns=["name", "latest", "fan_in"])
cand = pop[pop["latest"].fillna("").str.contains("security", case=False)]


def check(name):
    url = "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@/")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "UCN-research/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
    except Exception:
        return name, None, False
    text = f"{d.get('description') or ''} {d.get('readme') or ''}".lower()
    accounts = {m.get("name") for m in d.get("maintainers") or [] if isinstance(m, dict)}
    confirmed = "security holding package" in text or bool(accounts & {"npm", "npm-support"})
    return name, (d.get("dist-tags") or {}).get("latest"), confirmed


with ThreadPoolExecutor(16) as ex:
    res = pd.DataFrame(list(ex.map(check, cand["name"])), columns=["name", "latest_now", "confirmed"])
res = res.merge(cand, on="name")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
res.to_csv(OUT_CSV, index=False)
print(f"{len(res):,} packages; confirmed as npm placeholders: {int(res.confirmed.sum()):,}")
print(res[~res.confirmed].sort_values("fan_in", ascending=False).head(30).to_string(index=False))

known = set(CONFIRMED.read_text(encoding="utf-8").split()) if CONFIRMED.exists() else set()
new = set(res.loc[res.confirmed, "name"])
CONFIRMED.parent.mkdir(parents=True, exist_ok=True)
CONFIRMED.write_text("\n".join(sorted(known | new)) + "\n", encoding="utf-8")
print(f"\n{CONFIRMED}: {len(known | new):,} names, {len(new - known):,} new")