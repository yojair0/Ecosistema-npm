#!/usr/bin/env python3
"""
Pass 08 -- Correlations in the three situations of the inclusion population.

Reads the populations written by 07b_inclusion_population.py and compares,
side by side:
  A      with families, raw fan-in
  A_ext  with families, fan-in from other scopes only, so a family does not
         inflate its own members
  B      without families (scopes with 2 or more packages removed), raw fan-in

For each situation: packages by stratum, global correlations with fan-in,
correlations and medians within each stratum. Age is not a filter: it is a
variable, and its groups are tabulated to judge whether it could stratify
later. With millions of packages every correlation is significant, so cells
give Spearman's rho with the half-width of its 95% interval.

Input : data/07_inclusion_packages/population_with_families.parquet
        data/07_inclusion_packages/population_without_families.parquet
Output: data/07_inclusion_packages/comparison_report.md
"""
import time
import warnings

import numpy as np
import pandas as pd

DIR = "data/07_inclusion_packages"
SNAPSHOT = pd.Timestamp("2026-09-18")
STRATA = ["0a isolated", "0b consumer", "1-9", "10-99", "100-999", ">=1000"]
AGE_EDGES = [0, 365, 3 * 365, 6 * 365, np.inf]
AGE_GROUPS = ["under 1 year", "1-3 years", "3-6 years", "over 6 years"]
VARIABLES = ["n_versions", "n_maintainers", "n_keywords", "file_count", "unpacked",
             "age_days", "deprecated", "has_github", "fan_out", "fan_out_dev", "fan_in_dev"]
COLUMNS = ["created_date", "fan_in", "fan_in_external", "fan_out", "fan_in_dev", "fan_out_dev",
           "n_versions", "n_maintainers", "n_keywords", "file_count", "unpacked",
           "deprecated", "has_github"]


def md_table(header, rows):
    out = ["| " + " | ".join(str(h) for h in header) + " |", "|" + "---|" * len(header)]
    return "\n".join(out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]) + "\n"


def stratum(fi, fo):
    return np.select([(fi == 0) & (fo == 0), fi == 0, fi < 10, fi < 100, fi < 1000],
                     STRATA[:5], default=STRATA[5])


def spearman(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    n = int(m.sum())
    if n < 10:
        return "-"
    rx, ry = pd.Series(x[m]).rank().to_numpy(), pd.Series(y[m]).rank().to_numpy()
    if rx.std() == 0 or ry.std() == 0:
        return "-"
    rho = float(np.corrcoef(rx, ry)[0, 1])
    z, h = np.arctanh(np.clip(rho, -0.999999, 0.999999)), 1.96 * 1.06 / np.sqrt(n - 3)
    return f"{rho:+.3f} ±{(np.tanh(z + h) - np.tanh(z - h)) / 2:.3f}"


def load(path):
    d = pd.read_parquet(path, columns=COLUMNS)
    v = {c: pd.to_numeric(d[c], errors="coerce").to_numpy(dtype=float)
         for c in COLUMNS if c != "created_date"}
    v["age_days"] = (SNAPSHOT - pd.to_datetime(d["created_date"])).dt.days.to_numpy(dtype=float)
    return v


def main():
    warnings.filterwarnings("ignore")
    print("loading populations")
    a = load(f"{DIR}/population_with_families.parquet")
    b = load(f"{DIR}/population_without_families.parquet")
    situations = {"A": (a, a["fan_in"]), "A_ext": (a, a["fan_in_external"]), "B": (b, b["fan_in"])}
    strata = {k: stratum(t, v["fan_out"]) for k, (v, t) in situations.items()}

    print("correlations")
    counts = [[s] + [f"{int((strata[k] == s).sum()):,}" for k in situations] for s in STRATA]
    counts.append(["total"] + [f"{len(v['fan_in']):,}" for v, _ in situations.values()])
    global_rows = [[x] + [spearman(v[x], t) for v, t in situations.values()] for x in VARIABLES]

    def within(k, target_name):
        v, t = situations[k]
        target = t if target_name == "fan_in" else v["fan_out"]
        return [[x] + [spearman(v[x][strata[k] == s], target[strata[k] == s]) for s in STRATA]
                for x in VARIABLES if x != target_name]

    def profile(k):
        v = situations[k][0]
        rows = []
        for s in STRATA:
            m = strata[k] == s
            if not m.any():
                rows.append([s, "0"] + ["-"] * 5)
                continue
            med = lambda x: np.nanmedian(v[x][m])
            rows.append([s, f"{int(m.sum()):,}", f"{med('n_versions'):g}", f"{med('file_count'):g}",
                         f"{med('age_days') / 365:.1f}",
                         f"{np.nanmean(v['has_github'][m]) * 100:.1f}%", f"{med('fan_out'):g}"])
        return rows

    groups = np.asarray(pd.cut(a["age_days"], AGE_EDGES, right=False, labels=AGE_GROUPS)
                        .astype(object))
    age_rows = [[s] + [f"{int(((strata['A'] == s) & (groups == g)).sum()):,}" for g in AGE_GROUPS]
                for s in STRATA]
    adoption = [[g, f"{int((groups == g).sum()):,}",
                 f"{np.mean(a['fan_in'][groups == g] > 0) * 100:.1f}%",
                 f"{np.mean(a['fan_in_external'][groups == g] > 0) * 100:.1f}%"] for g in AGE_GROUPS]

    keys = list(situations)
    lines = [
        "# Correlations in three situations\n",
        f"Generated {time.strftime('%Y-%m-%d %H:%M')}. A: with families, raw fan-in. A_ext: "
        "with families, fan-in from other scopes only. B: without families, raw fan-in.\n",
        "## Packages by stratum\n",
        md_table(["Stratum"] + keys, counts),
        "## Global correlation with fan-in\n",
        md_table(["Variable"] + keys, global_rows),
    ]
    for k in keys:
        lines += [f"## Within each stratum: {k}\n", "### With fan-in\n",
                  md_table(["Variable"] + STRATA, within(k, "fan_in")),
                  "### With fan-out\n", md_table(["Variable"] + STRATA, within(k, "fan_out")),
                  "### Profile (medians; age in years)\n",
                  md_table(["Stratum", "Packages", "Versions", "Files", "Age", "GitHub",
                            "Fan-out"], profile(k))]
    lines += [
        "## Age groups (population A)\n",
        "Not a filter; shown to judge whether age could stratify later.\n",
        md_table(["Stratum"] + AGE_GROUPS, age_rows),
        md_table(["Age group", "Packages", "With dependents (raw)",
                  "With dependents from other scopes"], adoption),
    ]
    with open(f"{DIR}/comparison_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"done: {DIR}/comparison_report.md")


if __name__ == "__main__":
    main()