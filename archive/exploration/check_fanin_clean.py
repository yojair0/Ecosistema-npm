#!/usr/bin/env python3
"""
check_fanin_clean.py -- How much of the Fan-In comes from packages that the
inclusion rules excluded.

The fan_in of the populations counts dependents from the whole registry, so a
package can have fan_in > 0 only because excluded packages (spam with missing
dependencies, for example) depend on it. This script recounts each package's
production Fan-In using only dependents that are in population A, and reports
how many packages of the Fan-In > 0 population would drop to 0 or change band.

It does not modify any population file. Run it from the repository root,
wherever the script is stored:
    python archive/exploration/check_fanin_clean.py

Input : data/pasada2/*.jsonl  (the production dependencies of each package,
        the same source that pass 3 uses to count the Fan-In)
        data/07_inclusion_packages/inclusion_flags.parquet
Output: data/exploration/fanin_clean/fanin_clean.parquet  (name, fan_in, fan_in_clean, in_B)
        data/exploration/fanin_clean/report.md
"""
import collections
import glob
import json
import sys
import time
from pathlib import Path

import pandas as pd



def repo_root():
    """The folder that holds data/07_inclusion_packages: the current one or a parent
    of this script, so the script works from exploration/ or archive/exploration/."""
    for p in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (p / "data" / "07_inclusion_packages").is_dir():
            return p
    sys.exit("data/07_inclusion_packages not found: run from the repository root")


BASE = repo_root()
PASS2 = BASE / "data" / "pasada2"
FLAGS = BASE / "data" / "07_inclusion_packages" / "inclusion_flags.parquet"
OUT = BASE / "data" / "exploration" / "fanin_clean"
BANDS = [(0, 0, "0"), (1, 9, "1-9"), (10, 99, "10-99"), (100, 999, "100-999"),
         (1000, None, "1000+")]


def band(values):
    out = pd.Series("", index=values.index)
    for lo, hi, label in BANDS:
        out[(values >= lo) if hi is None else values.between(lo, hi)] = label
    return out


def fmt(n):
    return f"{int(n):,}".replace(",", ".")


def pct(part, total):
    return f"{part / total * 100:.1f}%".replace(".", ",") if total else "0%"


def section(df, title):
    n = len(df)
    if n == 0:
        return f"## {title}\n\nNo packages.\n"
    drops = int((df["fan_in_clean"] == 0).sum())
    moved = int((band(df["fan_in"]) != band(df["fan_in_clean"])).sum())
    lines = [f"## {title}\n",
             f"- Packages with fan_in > 0: {fmt(n)}",
             f"- With fan_in_clean = 0 (only excluded packages depend on them): "
             f"{fmt(drops)} ({pct(drops, n)})",
             f"- Change Fan-In band: {fmt(moved)} ({pct(moved, n)})\n",
             "| Band by fan_in | Packages | Drop to 0 | Change band |",
             "|---|---|---|---|"]
    b = band(df["fan_in"])
    changed = b != band(df["fan_in_clean"])
    for _, _, label in BANDS[1:]:
        m = b == label
        lines.append(f"| {label} | {fmt(m.sum())} | {fmt((m & (df.fan_in_clean == 0)).sum())} "
                     f"| {fmt((m & changed).sum())} |")
    return "\n".join(lines) + "\n"


def main():
    t0 = time.time()
    flags = pd.read_parquet(FLAGS, columns=["name", "fan_in", "in_A", "in_B"])
    in_a = set(flags.loc[flags["in_A"], "name"])
    print(f"Population A: {len(in_a):,} packages")

    # Same rule as pass 3: names in lower case, records with an error or
    # without a version have no production dependencies.
    shards = sorted(glob.glob(str(PASS2 / "*.jsonl")))
    if not shards:
        sys.exit(f"no pass 2 shards in {PASS2}")
    clean = collections.Counter()
    for k, path in enumerate(shards, 1):
        with open(path, encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                if "error" in d or d.get("sin_version"):
                    continue
                src = d["name"].strip().lower()
                if src not in in_a:
                    continue
                for dst in d.get("deps") or []:
                    dst = dst.strip().lower()
                    if dst != src:
                        clean[dst] += 1
        if k % 10 == 0 or k == len(shards):
            print(f"  {k}/{len(shards)} shards | {(time.time() - t0) / 60:.1f} min")

    study = flags[flags["in_A"] & (flags["fan_in"] > 0)].copy()
    study["fan_in_clean"] = study["name"].map(clean).fillna(0).astype("int32")
    above = int((study["fan_in_clean"] > study["fan_in"]).sum())

    OUT.mkdir(parents=True, exist_ok=True)
    study[["name", "fan_in", "fan_in_clean", "in_B"]].to_parquet(OUT / "fanin_clean.parquet",
                                                                 index=False)
    report = ["# Fan-In counted only with dependents in population A\n",
              f"Generated {time.strftime('%Y-%m-%d %H:%M')}. `fan_in` counts dependents from the "
              "whole registry; `fan_in_clean` counts only those in population A.\n",
              section(study, "With families (population A, fan_in > 0)"),
              section(study[study["in_B"]], "Without families (population B, fan_in > 0)"),
              f"Check: packages with fan_in_clean > fan_in (should be 0): {fmt(above)}.\n"]
    (OUT / "report.md").write_text("\n".join(report), encoding="utf-8")
    print(f"Done in {(time.time() - t0) / 60:.1f} min: {OUT / 'report.md'}")


if __name__ == "__main__":
    main()