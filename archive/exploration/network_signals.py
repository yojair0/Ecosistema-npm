#!/usr/bin/env python3
"""
Pass 7b -- Network signals and sampling frame for the strata pass.

Computes, for every node of the dependency network, columns that the strata
pass can join by name: declared and missing dependencies, fan-in variants
(raw, same scope, out of scope, from flagged packages, clean), time signals
on each package's dependents, and one boolean column per exclusion rule.
No package is removed. It then builds the sampling frame: how many packages
each stratum has, how many each rule excludes, and how many remain eligible.

Changes in version 2:
  - A package repeated in pass 2 is read once. Version 1 counted the
    dependencies of repeated packages twice (1,343 edges).
  - A burst of dependents marks a package as a coordinated core only when
    the package was born with them. An older package that received a burst
    later is a victim: it stays in the frame, and the burst dependents are
    still flagged, so its clean fan-in leaves them out.
  - The platform-binary pattern covers more Rust architectures (arm,
    powerpc, mips, sparc, thumb, riscv32). The short ones must be followed
    by a vendor field, so that names like "arm-sdk" are not caught.
  - Sampling frame by stratum, and figures.

Changes in version 3:
  - A burst victim is a package that already existed for at least a year
    when the burst of dependents arrived, measured from the median creation
    date of its dependents. Version 2 used the share of dependents born
    within 120 days of the package, which also let through 2024 spam cores
    whose dependents were created months before or after them.

Changes in version 4:
  - A victim's burst no longer counts in its clean fan-in, whether or not
    the burst dependents are flagged by another rule. Hundreds of dependents
    that appear together and never again are not independent adoption, as
    with dependents from the same family. Version 3 removed only the burst
    dependents flagged as colluded, so a victim like "confidence" kept a
    fan-in made almost entirely of its burst.

Changes in version 5:
  - The architecture of a Rust target may also follow a dot, as in
    "@rustbin/cargo.target.x86_64-unknown-linux-gnu" (168 packages that
    version 4 missed).

Rules and thresholds are fixed in the constants below. The coordinated
adoption thresholds were proposed after inspecting known spam networks, so
the script also writes a sensitivity grid over alternative thresholds and a
reference check: well-known packages must never be flagged by a spam rule.

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
        data/07_strata_analysis/frame_by_stratum.csv
        data/07_strata_analysis/signals_report.md
        data/07_strata_analysis/figures/*.png
"""
import glob
import json
import os
import re
import time
import zlib
from array import array

import numpy as np
import pandas as pd

PROFILE = "../data/06_profile_analysis/profile_table.parquet"
DEPS = "../data/pasada2/*.jsonl"
SHARDS = "../data/04_profile/part*/*.jsonl"
OUT = "../data/07_strata_analysis"
FIGURES = f"{OUT}/figures"
SNAPSHOT = pd.Timestamp("2026-09-18")

DECLARER_SHARE = 0.5      # more than half of declared dependencies missing
DECLARER_MIN = 10         # ... with at least this many declared
PROPAGATED_SHARE = 0.5    # more than half of fan-in from declarers
CORE_MIN_DEPS = 20        # dated out-of-scope dependents
CORE_SPAN_DAYS = 120      # 5th-95th percentile spread of their creation dates
CORE_MAX_RECENT = 0.005   # share of dependents created in the last year
CORE_MIN_AGE = 365        # the package had at least a year to keep growing
VICTIM_MIN_LAG = 365      # a victim existed this long before its dependents' median date
BURST_MARGIN = 60         # days added on each side of a victim's burst window
COLLUDED_SHARE = 0.5      # share of a dependent's links that point to bursts
MIN_AGE_FRAME = 365       # eligibility: at least one year old at the snapshot
FRAME_STRATUM = "stratum_clean_out_of_scope"

STRATA = ["0a isolated", "0b consumer", "1-9", "10-99", "100-999", ">=1000"]
STRATA_ES = {"0a isolated": "0a aislados", "0b consumer": "0b consumidores",
             ">=1000": "1,000 o más"}
REFERENCE = ["react", "lodash", "chalk", "cors", "ms", "strip-ansi", "debug",
             "express", "axios", "commander", "tslib", "@babel/core",
             "@stdlib/math-base-special-pow"]
# Main exclusion reason, in order of priority: a package flagged by several
# rules is counted under the first one, so that the reasons add up.
REASONS = {"security_placeholder": "Reemplazo de seguridad",
           "platform_binary": "Binario de plataforma",
           "types_only": "@types",
           "spam_declarer": "Spam declarador",
           "spam_propagated": "Spam propagado",
           "coordinated_core": "Núcleo coordinado",
           "colluded_dependent": "Dependiente coludido"}
BUCKETS = ["10-19", "20-49", "50-99", "100+"]
PERIODS = ["2011-2019", "2020-2023", "2024", "2025-2026"]
SHARE_BINS = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
SHARE_LABELS = ["0-10%", "10-30%", "30-50%", "50-70%", "70-90%", "90-100%"]
DECLARED_GROUPS = ["1-4", "5-9", "10-49", "50+"]

OS_ARCH = re.compile(
    r"(?:linux|darwin|win32|windows|freebsd|openbsd|netbsd|android|sunos|aix)"
    r"-(?:x64|x86|ia32|arm|arm64|ppc64|s390x|riscv64|loong64|mips64el|universal)")
_RUST_LONG = r"x86_64|aarch64|i686|i586|armv7|riscv64gc|powerpc64le|s390x|loongarch64|wasm32"
_RUST_SHORT = r"arm|armv5te|armebv7r|thumbv\w+|powerpc64|powerpc|mips\w*|sparc\w*|riscv32\w*|nvptx64"
RUST = re.compile(
    rf"(?:^|[-_/.])(?:(?:{_RUST_LONG})-|(?:{_RUST_SHORT})-(?:unknown|apple|pc|none|sun|linux|wrs)-)")

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
    out = ["| " + " | ".join(str(h) for h in header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def build_edges(index, n):
    """Production edges between nodes, plus declared and missing counts.

    A package that appears more than once in pass 2 is read only once.
    """
    src, dst = array("i"), array("i")
    declared = np.zeros(n, np.int64)
    missing = np.zeros(n, np.int64)
    seen = np.zeros(n, bool)
    repeated = 0
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
                if seen[s]:
                    repeated += 1
                    continue
                seen[s] = True
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
            declared, missing, repeated)


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
    """Days between the 5th and 95th percentile of dependents' creation,
    the median creation day, and the days of those two percentiles."""
    keep = (np.bincount(d_dst, minlength=n) >= min_count)[d_dst]
    dd, cc = d_dst[keep], d_cs[keep]
    span = np.full(n, -1, dtype=np.int64)
    median = np.full(n, -1, dtype=np.int64)
    first = np.full(n, -1, dtype=np.int64)
    last = np.full(n, -1, dtype=np.int64)
    if len(dd) == 0:
        return span, median, first, last
    order = np.lexsort((cc, dd))
    dd, cc = dd[order], cc[order]
    starts = np.r_[0, np.flatnonzero(np.diff(dd)) + 1]
    counts = np.diff(np.r_[starts, len(dd)])
    lo = starts + np.floor(0.05 * (counts - 1)).astype(np.int64)
    hi = starts + np.ceil(0.95 * (counts - 1)).astype(np.int64)
    span[dd[starts]] = cc[hi] - cc[lo]
    median[dd[starts]] = cc[starts + (counts - 1) // 2]
    first[dd[starts]] = cc[lo]
    last[dd[starts]] = cc[hi]
    return span, median, first, last


def make_figures(frame, baseline, missing_share, by_year, eligible_by_fan_in):
    """Five figures for the meeting and the document, labelled in Spanish."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        log("matplotlib is not installed, skipping figures (python -m pip install matplotlib)")
        return []
    os.makedirs(FIGURES, exist_ok=True)
    strata_es = [STRATA_ES.get(s, s) for s in STRATA]
    paths = []

    def save(fig, name):
        fig.tight_layout()
        path = f"{FIGURES}/{name}"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        paths.append(path)

    # 1. Share of each stratum excluded, by main reason
    fig, ax = plt.subplots(figsize=(9, 5))
    bottom = np.zeros(len(frame))
    size = frame["packages"].clip(lower=1).to_numpy()
    for col, label in REASONS.items():
        values = frame[col].to_numpy() / size * 100
        ax.bar(strata_es, values, bottom=bottom, label=label)
        bottom += values
    for i, total in enumerate(bottom):
        ax.text(i, total + 0.5, f"{total:.1f}%", ha="center", fontsize=9)
    ax.set_ylim(0, max(bottom.max() * 1.15, 1))
    ax.set_ylabel("% de los paquetes del estrato")
    ax.set_title("Qué parte de cada estrato se excluye, y por qué")
    ax.legend(fontsize=8)
    save(fig, "fig1_exclusions_by_stratum.png")

    # 2. How often the coordinated-adoption pattern appears, by period
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(BUCKETS))
    for i, period in enumerate(PERIODS):
        if period in baseline.index:
            values = baseline.loc[period].to_numpy(dtype=float)
            bars = ax.bar(x + (i - 1.5) * 0.2, values, 0.2, label=f"Creados en {period}")
            ax.bar_label(bars, labels=["" if np.isnan(v) else f"{v:.1f}" for v in values],
                         fontsize=7)
    ax.set_ylim(0, 110)
    ax.set_xlim(-0.6, len(BUCKETS) - 0.4)
    ax.set_xticks(x, ["10-19", "20-49", "50-99", "100 o más"])
    ax.set_xlabel("Dependientes de otras familias")
    ax.set_ylabel("% de los paquetes que cumple el patrón")
    ax.set_title("El patrón de adopción coordinada: raro por casualidad, casi total en 2024")
    ax.legend(fontsize=8, loc="upper left")
    save(fig, "fig2_coordinated_baseline.png")

    # 3. Share of missing dependencies, by number declared
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(SHARE_LABELS))
    for i, group in enumerate(DECLARED_GROUPS):
        values = missing_share[group].to_numpy()
        ax.bar(x + (i - 1.5) * 0.2, values, 0.2, label=f"Declaran {group}")
    ax.set_xlim(-0.6, len(SHARE_LABELS) - 0.4)
    ax.axvline(2.5, color="gray", linestyle="--")
    ax.text(2.55, ax.get_ylim()[1] * 0.92, "corte de 50%", color="gray", fontsize=9)
    ax.set_xticks(x, SHARE_LABELS)
    ax.set_xlabel("Proporción de sus dependencias que no existe")
    ax.set_ylabel("Paquetes")
    ax.set_title("Paquetes con al menos una dependencia inexistente")
    ax.legend(fontsize=8)
    save(fig, "fig3_missing_share.png")

    # 4. New rules by creation year
    fig, ax = plt.subplots(figsize=(9, 5))
    years = by_year.index.to_numpy()
    ax.bar(years - 0.2, by_year["colluded"], 0.4, label="Dependientes coludidos")
    ax.bar(years + 0.2, by_year["core"], 0.4, label="Núcleos coordinados")
    ax.set_yscale("log")
    ax.set_xlabel("Año de creación")
    ax.set_ylabel("Paquetes (escala logarítmica)")
    ax.set_title("Las reglas de adopción coordinada se concentran en 2024")
    ax.legend(fontsize=8)
    save(fig, "fig4_new_rules_by_year.png")

    # 5. Eligible packages per stratum under each fan-in
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(STRATA))
    versions = {"raw": "Fan-In bruto", "clean": "Sin spam",
                "clean_out_of_scope": "Sin spam ni misma familia"}
    for i, (key, label) in enumerate(versions.items()):
        ax.bar(x + (i - 1) * 0.27, eligible_by_fan_in[key].to_numpy(), 0.27, label=label)
    ax.set_yscale("log")
    ax.set_xticks(x, strata_es, rotation=15)
    ax.set_ylabel("Paquetes elegibles (escala logarítmica)")
    ax.set_title("Paquetes elegibles por estrato, según el Fan-In usado")
    ax.legend(fontsize=8)
    save(fig, "fig5_eligible_by_fan_in.png")
    return paths


def main():
    os.makedirs(OUT, exist_ok=True)
    log("loading profile table")
    prof = pd.read_parquet(PROFILE, columns=["name", "fan_in", "fan_out", "n_versions",
                                             "age_days", "created_year"])
    names = prof["name"].to_numpy(dtype=object)
    n = len(names)
    index = {name: i for i, name in enumerate(names)}

    log("reading production dependencies (a few minutes)")
    src, dst, declared, missing, repeated = build_edges(index, n)
    present = declared - missing
    log(f"  {len(src):,} edges between nodes, {repeated:,} repeated records skipped")

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
    old_enough = np.nan_to_num(age, nan=-1.0) >= MIN_AGE_FRAME
    year = prof["created_year"].to_numpy(dtype=float)
    one_version = prof["n_versions"].to_numpy(dtype=float) == 1

    # ------------------------------------------------ name-based rules
    name_s = pd.Series(names)
    types_only = name_s.str.startswith("@types/").to_numpy()
    os_arch = name_s.str.contains(OS_ARCH).to_numpy()
    rust = name_s.str.contains(RUST).to_numpy()
    platform_binary = os_arch | rust
    rustbin = name_s.str.startswith("@rustbin/").to_numpy()
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
    dep_span, dep_median, dep_p05, dep_p95 = spread_p05_p95(d_dst, d_cs, n, min_count=10)
    dep_one_version_share = count_by(dst, one_version[src], n) / np.maximum(fan_in_raw, 1)
    dep_fan_in_zero_share = count_by(dst, fan_in_raw[src] == 0, n) / np.maximum(fan_in_raw, 1)
    recent_share = dep_recent / np.maximum(dep_dated, 1)
    born_with = dep_within[120] / np.maximum(dep_dated, 1)
    burst_lag = np.where((dep_median >= 0) & (created >= 0), dep_median - created, -10**6)

    def burst_rule(min_deps, span_days, max_recent):
        """Dependents arrived in one short burst and stopped."""
        return ((dep_dated >= min_deps) & (dep_span >= 0) & (dep_span <= span_days)
                & (recent_share <= max_recent) & age_ok)

    def colluded_rule(targets, share):
        """One version, nobody depends on it, links mostly to burst targets."""
        to_target = count_by(src, targets[dst], n)
        return (one_version & (fan_in_raw == 0) & (to_target > 0)
                & (to_target / np.maximum(present, 1) >= share) & ~targets)

    coordinated_burst = burst_rule(CORE_MIN_DEPS, CORE_SPAN_DAYS, CORE_MAX_RECENT)
    burst_victim = coordinated_burst & (burst_lag >= VICTIM_MIN_LAG)
    coordinated_core = coordinated_burst & ~burst_victim
    colluded_dependent = colluded_rule(coordinated_burst, COLLUDED_SHARE)
    spam_any = spam_declarer | spam_propagated | coordinated_core | colluded_dependent
    excluded_any = spam_any | types_only | platform_binary | security_placeholder

    # ------------------------------------------------- fan-in variants
    # Edges that belong to a victim's burst: out-of-scope dependents created
    # inside the burst window, widened by a margin on each side.
    in_burst = (burst_victim[dst] & ~same & (cs >= 0)
                & (cs >= dep_p05[dst] - BURST_MARGIN) & (cs <= dep_p95[dst] + BURST_MARGIN))
    fan_in_same_scope = count_by(dst, same, n)
    fan_in_out_of_scope = fan_in_raw - fan_in_same_scope
    fan_in_from_flagged = count_by(dst, spam_any[src], n)
    fan_in_burst = count_by(dst, in_burst, n)
    fan_in_clean = count_by(dst, ~spam_any[src] & ~in_burst, n)
    fan_in_clean_out_of_scope = count_by(dst, ~same & ~spam_any[src] & ~in_burst, n)
    strata = {"raw": stratum(fan_in_raw, fo03),
              "clean": stratum(fan_in_clean, fo03),
              "clean_out_of_scope": stratum(fan_in_clean_out_of_scope, fo03)}

    # ------------------------------------------------- sampling frame
    log("building the sampling frame")
    flags = {"security_placeholder": security_placeholder, "platform_binary": platform_binary,
             "types_only": types_only, "spam_declarer": spam_declarer,
             "spam_propagated": spam_propagated, "coordinated_core": coordinated_core,
             "colluded_dependent": colluded_dependent}
    reason = np.full(n, "", dtype=object)
    for col in reversed(list(REASONS)):
        reason[flags[col]] = col
    eligible = ~excluded_any & old_enough
    base = strata["clean_out_of_scope"]
    rows = []
    for s in STRATA:
        m = base == s
        row = {"stratum": s, "packages": int(m.sum())}
        row.update({col: int((m & (reason == col)).sum()) for col in REASONS})
        row["excluded"] = int((m & excluded_any).sum())
        row["under_one_year"] = int((m & ~excluded_any & ~old_enough).sum())
        row["eligible"] = int((m & eligible).sum())
        rows.append(row)
    frame = pd.DataFrame(rows)
    frame["pct_excluded"] = (frame["excluded"] / frame["packages"].clip(lower=1) * 100).round(1)
    frame.to_csv(f"{OUT}/frame_by_stratum.csv", index=False)
    eligible_by_fan_in = pd.DataFrame(
        {k: [int(((v == s) & eligible).sum()) for s in STRATA] for k, v in strata.items()},
        index=STRATA)

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

    grid = []
    with np.errstate(invalid="ignore"):
        for share in (0.3, 0.5, 0.7):
            for mn in (5, 10, 15):
                f = (declared >= mn) & (dangling_share > share)
                grid.append(grid_row("spam_declarer", f"share>{share}, deps>={mn}", f))
    for mn in (10, 20, 50):
        for sp in (60, 120, 180):
            for rc in (0.005, 0.02):
                grid.append(grid_row("coordinated_burst",
                                     f"deps>={mn}, span<={sp}d, recent<={rc}",
                                     burst_rule(mn, sp, rc)))
    for lag in (180, 365, 730):
        grid.append(grid_row("coordinated_core", f"burst, not a victim (lag<{lag}d)",
                             coordinated_burst & (burst_lag < lag)))
    for share in (0.3, 0.5, 0.7):
        grid.append(grid_row("colluded_dependent", f"share>={share}",
                             colluded_rule(coordinated_burst, share)))
    sens = pd.DataFrame(grid)
    sens.to_csv(f"{OUT}/signals_sensitivity.csv", index=False)

    # ---------------------------------------------- triage of the 801
    tri = np.isin(strata["raw"], ["100-999", ">=1000"]) & (fan_in_out_of_scope == 0)
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

    # ---------------------------------------------- data for the figures
    has10 = dep_dated >= 10
    b = pd.DataFrame({
        "flag": burst_rule(10, CORE_SPAN_DAYS, CORE_MAX_RECENT)[has10],
        "dependents": pd.cut(dep_dated[has10], [9, 19, 49, 99, 10**7], labels=BUCKETS),
        "period": pd.cut(year[has10], [2010, 2019, 2023, 2024, 2026], labels=PERIODS)})
    baseline = b.pivot_table(index="period", columns="dependents", values="flag",
                             aggfunc="mean", observed=True) * 100
    baseline.index, baseline.columns = baseline.index.astype(str), baseline.columns.astype(str)
    baseline = baseline.reindex(columns=BUCKETS)
    has_missing = missing > 0
    missing_share = pd.crosstab(
        pd.cut(dangling_share[has_missing], SHARE_BINS, labels=SHARE_LABELS),
        pd.cut(declared[has_missing], [0, 4, 9, 49, 10**6], labels=DECLARED_GROUPS))
    missing_share.index = missing_share.index.astype(str)
    missing_share.columns = missing_share.columns.astype(str)
    missing_share = missing_share.reindex(index=SHARE_LABELS, columns=DECLARED_GROUPS,
                                          fill_value=0)
    yr = pd.DataFrame({"year": year, "core": coordinated_core,
                       "colluded": colluded_dependent}).dropna(subset=["year"])
    by_year = yr.groupby(yr["year"].astype(int))[["core", "colluded"]].sum()
    log("drawing figures")
    figures = make_figures(frame, baseline, missing_share, by_year, eligible_by_fan_in)

    # ------------------------------------------------------- outputs
    log("writing outputs")
    pd.DataFrame({
        "name": names, "scope": scope.to_numpy(), "half": half,
        "deps_declared": declared, "deps_missing": missing, "dangling_share": dangling_share,
        "fan_in_raw": fan_in_raw, "fan_in_same_scope": fan_in_same_scope,
        "fan_in_out_of_scope": fan_in_out_of_scope, "fan_in_from_flagged": fan_in_from_flagged,
        "fan_in_victim_burst": fan_in_burst,
        "fan_in_clean": fan_in_clean, "fan_in_clean_out_of_scope": fan_in_clean_out_of_scope,
        "dep_dated": dep_dated, "dep_within_30": dep_within[30],
        "dep_within_90": dep_within[90], "dep_within_120": dep_within[120],
        "dep_span_p05_p95": dep_span, "dep_recent_365": dep_recent,
        "dep_before_target_1v": dep_before_1v, "born_with_package": born_with,
        "burst_lag_days": np.where(dep_median >= 0, burst_lag, np.nan),
        "dep_one_version_share": dep_one_version_share,
        "dep_fan_in_zero_share": dep_fan_in_zero_share,
        "spam_declarer": spam_declarer, "spam_propagated": spam_propagated,
        "types_only": types_only, "platform_binary": platform_binary,
        "security_placeholder": security_placeholder,
        "coordinated_burst": coordinated_burst, "coordinated_core": coordinated_core,
        "burst_victim": burst_victim, "colluded_dependent": colluded_dependent,
        "spam_any": spam_any, "excluded_any": excluded_any, "exclusion_reason": reason,
        "old_enough": old_enough, "eligible": eligible,
        "stratum_raw": strata["raw"], "stratum_clean": strata["clean"],
        "stratum_clean_out_of_scope": strata["clean_out_of_scope"],
    }).to_parquet(f"{OUT}/signals.parquet", index=False)

    rule_rows = [[r, f"{int(f.sum()):,}"] for r, f in [
        ("spam_declarer", spam_declarer), ("spam_propagated", spam_propagated),
        ("types_only", types_only), ("platform_binary (all)", platform_binary),
        ("platform_binary (Rust format only)", rust & ~os_arch),
        ("security_placeholder", security_placeholder),
        ("coordinated_burst (core or victim)", coordinated_burst),
        ("coordinated_core (excluded)", coordinated_core),
        ("burst_victim (kept, fan-in cleaned)", burst_victim),
        ("colluded_dependent", colluded_dependent), ("excluded_any", excluded_any)]]
    victims = pd.DataFrame({"name": names, "created_year": year, "fan_in_raw": fan_in_raw,
                            "burst": fan_in_burst, "flagged": fan_in_from_flagged,
                            "final": fan_in_clean_out_of_scope, "lag": burst_lag})[burst_victim]
    victims_by_year = victims["created_year"].value_counts().sort_index()
    victims = victims.sort_values("fan_in_raw", ascending=False).head(20)
    frame_cols = ["stratum", "packages"] + list(REASONS) + ["excluded", "pct_excluded",
                                                            "under_one_year", "eligible"]
    lines = [
        "# Network signals report\n",
        f"Generated {time.strftime('%Y-%m-%d %H:%M')} over {n:,} nodes and {len(src):,} edges.\n",
        "## Verification\n",
        f"- Records repeated in pass 2, read once: {repeated:,}.",
        f"- Fan-in recomputed from the edges differs from pass 03 in {mismatch:,} packages.",
        f"- Pass 03 fan-out equals declared dependencies in {fo_declared:.2f}% of packages, "
        f"and dependencies that exist in {fo_present:.2f}%.\n",
        "## Rules\n",
        md_table(["Rule", "Packages"], rule_rows),
        f"## Sampling frame (strata by {FRAME_STRATUM})\n",
        "Each excluded package is counted once, under its first reason in this order: "
        + ", ".join(REASONS) + f". Eligible: not excluded and at least {MIN_AGE_FRAME} days "
        "old at the snapshot.\n",
        md_table(frame_cols, frame[frame_cols].values.tolist()),
        "## Eligible packages under each fan-in\n",
        md_table(["Stratum"] + list(eligible_by_fan_in.columns),
                 [[s] + [f"{v:,}" for v in eligible_by_fan_in.loc[s]] for s in STRATA]),
        "## Largest burst victims (kept in the frame)\n",
        "Victims by creation year: " + ", ".join(
            f"{y:.0f}: {c:,}" for y, c in victims_by_year.items()) + "\n",
        "Fan-in for strata: without spam sources, same-scope dependents or the burst.\n",
        md_table(["Package", "Created", "Fan-in raw", "Burst dependents",
                  "From spam sources", "Fan-in for strata", "Burst arrived after (years)"],
                 [[r.name, f"{r.created_year:.0f}", f"{int(r.fan_in_raw):,}", f"{int(r.burst):,}",
                   f"{int(r.flagged):,}", f"{int(r.final):,}", f"{r.lag / 365:.1f}"]
                  for r in victims.itertuples()]),
        "## Reference packages (must all be False)\n",
        md_table(["Package", "spam_declarer", "spam_propagated", "coordinated_core",
                  "colluded_dependent"],
                 [[r, spam_declarer[index[r]], spam_propagated[index[r]],
                   coordinated_core[index[r]], colluded_dependent[index[r]]] for r in refs]),
        "## Sensitivity grid\n",
        md_table(list(sens.columns), sens.astype(str).values.tolist()),
        f"## @rustbin coverage\n\n{int(rustbin.sum()):,} packages, "
        f"{int((rustbin & ~platform_binary).sum()):,} not flagged as platform binaries.\n",
        f"## Triage: {len(t):,} packages in strata 100+ with no out-of-scope dependents\n",
        md_table(["Scope", "Packages", "Share flagged by any rule", "Share with one version",
                  "Max fan-in"],
                 [[s, int(r.packages), f"{r.any_rule:.0%}", f"{r.one_version:.0%}",
                   f"{int(r.max_fan_in):,}"] for s, r in by_scope.head(25).iterrows()]),
        "## Figures\n",
        "\n".join(f"- `{p}`" for p in figures) or "- not generated (matplotlib missing)",
    ]
    with open(f"{OUT}/signals_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log(f"done: {OUT}/signals_report.md")


if __name__ == "__main__":
    main()