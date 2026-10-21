#!/usr/bin/env python3
"""
Pass 7b -- Network signals for the strata pass.

Computes, for every node of the dependency network, columns that the strata
pass (07) can join by name: declared and missing dependencies, fan-in
variants (raw, same scope, out of scope, from flagged packages, clean), time
signals on each package's dependents, and one boolean column per exclusion
rule. No package is removed.

Rules and thresholds are fixed in the constants below. The coordinated
adoption thresholds were proposed after inspecting known spam networks, so
the script also writes a sensitivity grid over alternative thresholds, split
by a deterministic hash of the name, and a reference check: well-known
packages must never be flagged by a spam rule.

Time signals use the creation date of each dependent, not the date it
started depending on the package, which the data does not record. They are
computed on out-of-scope dependents only, so that a family publishing many
packages together is not mistaken for a coordinated network.

Input : data/06_profile_analysis/profile_table.parquet
        data/pasada2/*.jsonl            production dependencies
        data/04_profile/part*/*.jsonl   latest version, for placeholders
Output: data/07_strata_analysis/signals.parquet
        data/07_strata_analysis/signals_sensitivity.csv
        data/07_strata_analysis/signals_triage.csv
        data/07_strata_analysis/signals_report.md
"""
import glob
import json
import re
import time
import zlib
from array import array

import numpy as np
import pandas as pd

PROFILE = "data/06_profile_analysis/profile_table.parquet"
DEPS = "data/pasada2/*.jsonl"
SHARDS = "data/04_profile/part*/*.jsonl"
OUT = "data/07_strata_analysis"
SNAPSHOT = pd.Timestamp("2026-09-18")

DECLARER_SHARE = 0.5      # more than half of declared dependencies missing
DECLARER_MIN = 10         # ... with at least this many declared
PROPAGATED_SHARE = 0.5    # more than half of fan-in from declarers
CORE_MIN_DEPS = 20        # dated out-of-scope dependents
CORE_SPAN_DAYS = 120      # 5th-95th percentile spread of their creation dates
CORE_MAX_RECENT = 0.005   # share of dependents created in the last year
CORE_MIN_AGE = 365        # the package had at least a year to keep growing
COLLUDED_SHARE = 0.5      # share of a dependent's links that point to cores

STRATA = ["0a isolated", "0b consumer", "1-9", "10-99", "100-999", ">=1000"]
REFERENCE = ["react", "lodash", "chalk", "cors", "ms", "strip-ansi", "debug",
             "express", "axios", "commander", "tslib", "@babel/core",
             "@stdlib/math-base-special-pow"]
OS_ARCH = re.compile(
    r"(?:linux|darwin|win32|windows|freebsd|openbsd|netbsd|android|sunos|aix)"
    r"-(?:x64|x86|ia32|arm|arm64|ppc64|s390x|riscv64|loong64|mips64el|universal)")
RUST = re.compile(
    r"(?:^|[-_/])(?:x86_64|aarch64|i686|i586|armv7|riscv64gc|powerpc64le|"
    r"s390x|loongarch64|wasm32)-")

T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.0f}s] {msg}", flush=True)


def norm(name):
    return name.strip().lower()


def count_by(target, mask, n):
    return np.bincount(target[mask], minlength=n).astype(np.int64)


def stratum(fi, fo):
    return np.select([(fi == 0) & (fo == 0), fi == 0, fi < 10, fi < 100,
                      fi < 1000], STRATA[:5], default=STRATA[5])


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def build_edges(index, n):
    """Production edges between nodes, plus declared and missing counts."""
    src, dst = array("i"), array("i")
    declared = np.zeros(n, np.int64)
    missing = np.zeros(n, np.int64)
    for path in sorted(glob.glob(DEPS)):
        with open(path, encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                deps = d.get("deps") or ()
                if not deps:
                    continue
                s = index.get(norm(d["name"]))
                if s is None:
                    continue
                miss = 0
                for x in deps:
                    t = index.get(norm(x))
                    if t is None:
                        miss += 1
                    else:
                        src.append(s)
                        dst.append(t)
                declared[s] = len(deps)
                missing[s] = miss
    return (np.frombuffer(src, dtype=np.int32), np.frombuffer(dst, dtype=np.int32),
            declared, missing)


def security_placeholders(index, n):
    flag = np.zeros(n, bool)
    for path in glob.glob(SHARDS):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if '"0.0.1-security' not in line:
                    continue
                d = json.loads(line)
                if (d.get("latest") or "").startswith("0.0.1-security"):
                    i = index.get(norm(d["name"]))
                    if i is not None:
                        flag[i] = True
    return flag


def spread_p05_p95(d_dst, d_cs, n, min_count):
    """Days between the 5th and 95th percentile of dependents' creation."""
    keep = (np.bincount(d_dst, minlength=n) >= min_count)[d_dst]
    dd, cc = d_dst[keep], d_cs[keep]
    span = np.full(n, -1, dtype=np.int64)
    if len(dd) == 0:
        return span
    order = np.lexsort((cc, dd))
    dd, cc = dd[order], cc[order]
    starts = np.r_[0, np.flatnonzero(np.diff(dd)) + 1]
    counts = np.diff(np.r_[starts, len(dd)])
    lo = starts + np.floor(0.05 * (counts - 1)).astype(np.int64)
    hi = starts + np.ceil(0.95 * (counts - 1)).astype(np.int64)
    span[dd[starts]] = cc[hi] - cc[lo]
    return span


def main():
    log("loading profile table")
    prof = pd.read_parquet(PROFILE, columns=["name", "fan_in", "fan_out",
                                             "n_versions", "age_days"])
    names = prof["name"].to_numpy(dtype=object)
    n = len(names)
    index = {name: i for i, name in enumerate(names)}

    log("reading production dependencies (a few minutes)")
    src, dst, declared, missing = build_edges(index, n)
    present = declared - missing
    log(f"  {len(src):,} edges between nodes")

    # ------------------------------------------------------ verification
    fan_in_raw = np.bincount(dst, minlength=n).astype(np.int64)
    fi03 = prof["fan_in"].to_numpy(dtype=np.int64)
    fo03 = prof["fan_out"].to_numpy(dtype=np.int64)
    mismatch = int((fan_in_raw != fi03).sum())
    fo_declared = float((fo03 == declared).mean() * 100)
    fo_present = float((fo03 == present).mean() * 100)

    # -------------------------------------------------- scope and dates
    scope = pd.Series(names).str.extract(r"^(@[^/]+)/", expand=False)
    scope_code = pd.factorize(scope)[0].astype(np.int32)
    same = (scope_code[src] == scope_code[dst]) & (scope_code[src] >= 0)
    snap = (SNAPSHOT - pd.Timestamp("1970-01-01")).days
    age = prof["age_days"].to_numpy(dtype=float)
    created = np.where(np.isnan(age), -1, snap - np.nan_to_num(age)).astype(np.int64)
    age_ok = np.nan_to_num(age, nan=-1.0) >= CORE_MIN_AGE
    one_version = prof["n_versions"].to_numpy(dtype=float) == 1

    # ------------------------------------------------ name-based rules
    name_s = pd.Series(names)
    types_only = name_s.str.startswith("@types/").to_numpy()
    os_arch = name_s.str.contains(OS_ARCH).to_numpy()
    rust = name_s.str.contains(RUST).to_numpy()
    platform_binary = os_arch | rust
    log("reading latest versions for security placeholders")
    security_placeholder = security_placeholders(index, n)

    # ---------------------------------------------- dependency spam rules
    with np.errstate(divide="ignore", invalid="ignore"):
        dangling_share = np.where(declared > 0, missing / np.maximum(declared, 1), np.nan)
        spam_declarer = (declared >= DECLARER_MIN) & (dangling_share > DECLARER_SHARE)
    from_declarer = count_by(dst, spam_declarer[src], n)
    spam_propagated = ((fan_in_raw > 0) & ~spam_declarer
                       & (from_declarer / np.maximum(fan_in_raw, 1) > PROPAGATED_SHARE))

    # ---------------------------------------------- time signals (out of scope)
    log("computing time signals on dependents")
    cs, cd = created[src], created[dst]
    dated = ~same & (cs >= 0) & (cd >= 0)
    d_dst, d_cs, d_src = dst[dated], cs[dated], src[dated]
    d_gap = d_cs - cd[dated]
    dep_dated = np.bincount(d_dst, minlength=n).astype(np.int64)
    dep_within = {w: count_by(d_dst, np.abs(d_gap) <= w, n) for w in (30, 90, 120)}
    dep_recent = count_by(d_dst, d_cs >= snap - 365, n)
    dep_before_1v = count_by(d_dst, (d_gap < -1) & one_version[d_src], n)
    dep_span = spread_p05_p95(d_dst, d_cs, n, min_count=10)
    dep_one_version_share = count_by(dst, one_version[src], n) / np.maximum(fan_in_raw, 1)
    dep_fan_in_zero_share = count_by(dst, fan_in_raw[src] == 0, n) / np.maximum(fan_in_raw, 1)
    recent_share = dep_recent / np.maximum(dep_dated, 1)

    def core_rule(min_deps, span_days, max_recent):
        return ((dep_dated >= min_deps) & (dep_span >= 0) & (dep_span <= span_days)
                & (recent_share <= max_recent) & age_ok)

    def colluded_rule(core, share):
        to_core = count_by(src, core[dst], n)
        return (one_version & (fan_in_raw == 0) & (to_core > 0)
                & (to_core / np.maximum(present, 1) >= share) & ~core)

    coordinated_core = core_rule(CORE_MIN_DEPS, CORE_SPAN_DAYS, CORE_MAX_RECENT)
    colluded_dependent = colluded_rule(coordinated_core, COLLUDED_SHARE)
    spam_any = spam_declarer | spam_propagated | coordinated_core | colluded_dependent
    excluded_any = spam_any | types_only | platform_binary | security_placeholder

    # ------------------------------------------------- fan-in variants
    fan_in_same_scope = count_by(dst, same, n)
    fan_in_out_of_scope = fan_in_raw - fan_in_same_scope
    fan_in_from_flagged = count_by(dst, spam_any[src], n)
    fan_in_clean = fan_in_raw - fan_in_from_flagged
    fan_in_clean_out_of_scope = count_by(dst, ~same & ~spam_any[src], n)
    stratum_raw = stratum(fan_in_raw, fo03)
    stratum_clean = stratum(fan_in_clean, fo03)
    stratum_clean_oos = stratum(fan_in_clean_out_of_scope, fo03)

    # ---------------------------------------------- sensitivity grid
    log("sensitivity grid")
    refs = [r for r in REFERENCE if r in index]
    ref_idx = np.array([index[r] for r in refs], dtype=np.int64)
    half = np.fromiter((zlib.crc32(s.encode()) & 1 for s in names), dtype=np.int8, count=n)
    high = fan_in_raw >= 100

    def grid_row(rule, params, flag):
        hit = [refs[k] for k in np.flatnonzero(flag[ref_idx])]
        return {"rule": rule, "params": params, "flagged": int(flag.sum()),
                "flagged_fan_in_100_plus": int((flag & high).sum()),
                "half_a": int((flag & (half == 0)).sum()),
                "half_b": int((flag & (half == 1)).sum()),
                "references_flagged": ", ".join(hit) or "none"}

    rows = []
    with np.errstate(invalid="ignore"):
        for share in (0.3, 0.5, 0.7):
            for mn in (5, 10, 15):
                f = (declared >= mn) & (dangling_share > share)
                rows.append(grid_row("spam_declarer", f"share>{share}, deps>={mn}", f))
    for mn in (10, 20, 50):
        for sp in (60, 120, 180):
            for rc in (0.005, 0.02):
                rows.append(grid_row("coordinated_core",
                                     f"deps>={mn}, span<={sp}d, recent<={rc}",
                                     core_rule(mn, sp, rc)))
    for share in (0.3, 0.5, 0.7):
        rows.append(grid_row("colluded_dependent", f"share>={share}",
                             colluded_rule(coordinated_core, share)))
    sens = pd.DataFrame(rows)
    sens.to_csv(f"{OUT}/signals_sensitivity.csv", index=False)

    # ---------------------------------------------- triage of the 801
    tri = np.isin(stratum_raw, ["100-999", ">=1000"]) & (fan_in_out_of_scope == 0)
    t = pd.DataFrame({
        "name": names[tri], "scope": scope.to_numpy()[tri],
        "fan_in_raw": fan_in_raw[tri], "one_version": one_version[tri],
        "spam_any": spam_any[tri], "excluded_any": excluded_any[tri],
    })
    t["scope"] = t["scope"].fillna("(no scope)")
    t.to_csv(f"{OUT}/signals_triage.csv", index=False)
    by_scope = (t.groupby("scope")
                 .agg(packages=("name", "size"), any_rule=("excluded_any", "mean"),
                      one_version=("one_version", "mean"), max_fan_in=("fan_in_raw", "max"))
                 .sort_values("packages", ascending=False))

    # ------------------------------------------------------- outputs
    log("writing outputs")
    pd.DataFrame({
        "name": names, "scope": scope.to_numpy(), "half": half,
        "deps_declared": declared, "deps_missing": missing, "dangling_share": dangling_share,
        "fan_in_raw": fan_in_raw, "fan_in_same_scope": fan_in_same_scope,
        "fan_in_out_of_scope": fan_in_out_of_scope, "fan_in_from_flagged": fan_in_from_flagged,
        "fan_in_clean": fan_in_clean, "fan_in_clean_out_of_scope": fan_in_clean_out_of_scope,
        "dep_dated": dep_dated, "dep_within_30": dep_within[30],
        "dep_within_90": dep_within[90], "dep_within_120": dep_within[120],
        "dep_span_p05_p95": dep_span, "dep_recent_365": dep_recent,
        "dep_before_target_1v": dep_before_1v,
        "dep_one_version_share": dep_one_version_share,
        "dep_fan_in_zero_share": dep_fan_in_zero_share,
        "spam_declarer": spam_declarer, "spam_propagated": spam_propagated,
        "types_only": types_only, "platform_binary": platform_binary,
        "security_placeholder": security_placeholder,
        "coordinated_core": coordinated_core, "colluded_dependent": colluded_dependent,
        "spam_any": spam_any, "excluded_any": excluded_any,
        "stratum_raw": stratum_raw, "stratum_clean": stratum_clean,
        "stratum_clean_out_of_scope": stratum_clean_oos,
    }).to_parquet(f"{OUT}/signals.parquet", index=False)

    rules = [("spam_declarer", spam_declarer), ("spam_propagated", spam_propagated),
             ("types_only", types_only), ("platform_binary (all)", platform_binary),
             ("platform_binary (Rust format only)", rust & ~os_arch),
             ("security_placeholder", security_placeholder),
             ("coordinated_core", coordinated_core),
             ("colluded_dependent", colluded_dependent), ("excluded_any", excluded_any)]
    ref_rows = [[r] + [str(bool(flag[index[r]])) for _, flag in rules[:2] + rules[6:8]]
                for r in refs]
    strata_rows = [[s, f"{int((stratum_raw == s).sum()):,}",
                    f"{int((stratum_clean == s).sum()):,}",
                    f"{int((stratum_clean_oos == s).sum()):,}"] for s in STRATA]
    lines = [
        "# Network signals report\n",
        f"Generated {time.strftime('%Y-%m-%d %H:%M')} over {n:,} nodes and {len(src):,} edges.\n",
        "## Verification\n",
        f"- Fan-in recomputed from the edges differs from pass 03 in {mismatch:,} packages.",
        f"- Pass 03 fan-out equals declared dependencies in {fo_declared:.2f}% of packages, "
        f"and dependencies that exist in {fo_present:.2f}%.\n",
        "## Rules\n",
        md_table(["Rule", "Packages"], [[r, f"{int(f.sum()):,}"] for r, f in rules]),
        "## Strata under each fan-in\n",
        md_table(["Stratum", "Raw", "Clean", "Clean, out of scope"], strata_rows),
        "## Reference packages (must all be False)\n",
        md_table(["Package", "spam_declarer", "spam_propagated", "coordinated_core",
                  "colluded_dependent"], ref_rows),
        "## Sensitivity grid\n",
        md_table(list(sens.columns), sens.astype(str).values.tolist()),
        f"## Triage: {len(t):,} packages in strata 100+ with no out-of-scope dependents\n",
        md_table(["Scope", "Packages", "Share flagged by any rule", "Share with one version",
                  "Max fan-in"],
                 [[s, r.packages, f"{r.any_rule:.0%}", f"{r.one_version:.0%}",
                   f"{r.max_fan_in:,}"] for s, r in by_scope.head(25).iterrows()]),
    ]
    with open(f"{OUT}/signals_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log(f"done: {OUT}/signals_report.md")


if __name__ == "__main__":
    main()