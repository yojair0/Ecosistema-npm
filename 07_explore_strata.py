#!/usr/bin/env python3
"""
Pass 7 -- Strata exploration and validation.

Produces the evidence needed to decide the stratification:

  1. exclusions: spam suspects, packages whose fan-in comes mostly from
     spam, TypeScript declaration packages and platform-specific binaries
  2. log-decade strata on fan-in, with fan-in = 0 split into isolated
     packages and pure consumers, and eligibility per stratum
  3. clustering on the full topological profile (fan-in and fan-out of
     every dependency type), to test whether packages separate into roles

The choice of k in section 3 is fixed in advance: the highest silhouette
between 2 and 8. Silhouette is read with the usual thresholds (Kaufman and
Rousseeuw): above 0.50 reasonable structure, 0.26 to 0.50 weak, 0.25 or
below no substantial structure.

Name-based exclusions are pre-filters. Whether a package holds JavaScript
that can be analysed is settled later, on its published tarball.

Input : results/profile_table.parquet   (pass 06)
        data/pasada2/*.jsonl             (dependency lists, pass 02)
Output: results/strata_report.md
        results/strata_table.parquet
"""
import glob
import json
import re
import time
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

TABLE = "results/profile_table.parquet"
DEPS_DIR = "data/pasada2"
OUT_MD = "results/strata_report.md"
OUT_TABLE = "results/strata_table.parquet"

SPAM_SHARE = 0.5      # more than half of the declared dependencies missing
SPAM_MIN_DEPS = 10    # below this, a single typo would flag a package
MIN_FILES = 5         # proxy for a minimum of internal modules
MIN_AGE = 365         # one-year window agreed in the meeting
K_RANGE = range(2, 9)
SIL_SAMPLE = 10_000
SEED = 42

TOPO = ["fan_in", "fan_in_dev", "fan_in_peer", "fan_in_opt",
        "fan_out", "fan_out_dev", "fan_out_peer", "fan_out_opt"]
STRATA = ["0a isolated", "0b consumer", "1-9", "10-99", "100-999", ">=1000"]
PLATFORM = re.compile(
    r"(linux|darwin|win32|windows|freebsd|openbsd|netbsd|android|sunos|aix)"
    r"-(x64|x86|ia32|arm|arm64|ppc64|s390x|riscv64|loong64|mips64el|universal)")
EXCLUSIONS = ["spam_suspect", "spam_propagated", "types_only", "platform_binary"]

T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.0f}s] {msg}", flush=True)


def norm(name):
    return name.strip().lower()


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def scan_dependencies(nodes):
    """One pass over the dependency lists.

    Returns declared and missing prod dependencies per package, and how many
    times each existing package is declared by a spam suspect. A package is
    a spam suspect on its own declarations alone, so both counts can be
    built in the same pass.
    """
    declared, missing, from_spam = {}, {}, Counter()
    for path in sorted(glob.glob(f"{DEPS_DIR}/*.jsonl")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                deps = d.get("deps") or []
                if not deps:
                    continue
                name = norm(d["name"])
                targets = [norm(x) for x in deps]
                miss = sum(1 for t in targets if t not in nodes)
                declared[name] = len(targets)
                missing[name] = miss
                if len(targets) >= SPAM_MIN_DEPS and miss / len(targets) > SPAM_SHARE:
                    for t in targets:
                        if t in nodes:
                            from_spam[t] += 1
    return declared, missing, from_spam


def main():
    lines = []
    w = lines.append

    log("loading profile table")
    df = pd.read_parquet(TABLE)
    nodes = set(df["package"])

    log("scanning dependency lists (a few minutes)")
    declared, missing, from_spam = scan_dependencies(nodes)
    df["n_deps_declared"] = df["package"].map(declared)
    df["n_deps_missing"] = df["package"].map(missing)
    df["dangling_share"] = df["n_deps_missing"] / df["n_deps_declared"]
    df["spam_suspect"] = ((df["dangling_share"] > SPAM_SHARE)
                          & (df["n_deps_declared"] >= SPAM_MIN_DEPS))
    df["fan_in_from_spam"] = df["package"].map(from_spam).fillna(0).astype(int)
    df["spam_propagated"] = ((df["fan_in"] > 0)
                             & (df["fan_in_from_spam"] / df["fan_in"].clip(lower=1)
                                > SPAM_SHARE)
                             & ~df["spam_suspect"])
    df["types_only"] = df["package"].str.startswith("@types/")
    df["platform_binary"] = df["package"].str.contains(PLATFORM, regex=True)
    df["excluded"] = df[EXCLUSIONS].any(axis=1)

    fi, fo = df["fan_in"], df["fan_out"]
    df["stratum_decade"] = np.select(
        [(fi == 0) & (fo == 0), fi == 0, fi < 10, fi < 100, fi < 1000],
        STRATA[:5], default=STRATA[5])

    size_ok = df["file_count"].isna() | (df["file_count"] >= MIN_FILES)
    df["eligible"] = (df["has_profile"] & (df["age_days"] >= MIN_AGE)
                      & (df["deprecated"] != 1) & ~df["excluded"] & size_ok)

    # --------------------------------------------------- 1. exclusions
    w("# Strata exploration report\n")
    w(f"Generated {time.strftime('%Y-%m-%d %H:%M')} from {len(df):,} nodes.\n")
    w("## 1. Exclusions\n")
    w(f"- **spam_suspect**: more than {SPAM_SHARE:.0%} of declared dependencies "
      f"point to names absent from the registry, with at least {SPAM_MIN_DEPS} "
      f"declared. Below that size a single typo would flag a package.\n"
      f"- **spam_propagated**: not a suspect itself, but more than "
      f"{SPAM_SHARE:.0%} of its fan-in comes from suspects. Spam packages "
      f"declare one another, so fan-in can be inflated artificially.\n"
      f"- **types_only**: `@types/` packages hold TypeScript declarations, "
      f"with no executable code.\n"
      f"- **platform_binary**: names with an operating-system and architecture "
      f"suffix, which ship compiled code.\n\n"
      f"The last two are name-based pre-filters; whether a package holds "
      f"analysable JavaScript is settled later on its tarball.\n")
    w(md_table(["Criterion", "Packages"], [
        ["missing share > 50%, any size (reference)",
         f"{int((df['dangling_share'] > SPAM_SHARE).sum()):,}"],
        *[[c, f"{int(df[c].sum()):,}"] for c in EXCLUSIONS],
        ["excluded by any criterion", f"{int(df['excluded'].sum()):,}"],
    ]))
    w("### Exclusions by stratum\n")
    w(md_table(["Stratum"] + EXCLUSIONS, [
        [s] + [f"{int(df.loc[df['stratum_decade'] == s, c].sum()):,}"
               for c in EXCLUSIONS]
        for s in STRATA]))

    # ----------------------------------------------- 2. decade strata
    w("## 2. Log-decade strata and eligibility\n")
    w(f"Eligible: has a profile, at least {MIN_AGE} days old at the snapshot, "
      f"not deprecated, not excluded, and at least {MIN_FILES} published files. "
      f"Packages without a file count, mostly old ones, are kept and counted "
      f"separately, since excluding them would bias against older packages.\n")
    rows = []
    for s in STRATA:
        sub = df[df["stratum_decade"] == s]
        el = sub["eligible"]
        unknown = int((el & sub["file_count"].isna()).sum())
        rows.append([s, f"{len(sub):,}", f"{int(sub['excluded'].sum()):,}",
                     f"{int(el.sum()):,} ({el.mean() * 100:.1f}%)",
                     f"{unknown:,}"])
    w(md_table(["Stratum", "Packages", "Excluded", "Eligible",
                "of which file count unknown"], rows))

    # --------------------------------------------- 3. role clustering
    log("clustering the topological profile")
    mask = df["has_profile"] & (df[TOPO].sum(axis=1) > 0)
    X = StandardScaler().fit_transform(
        np.log1p(df.loc[mask, TOPO].astype(float).to_numpy()))
    rng = np.random.default_rng(SEED)
    sample = rng.choice(len(X), size=min(SIL_SAMPLE, len(X)), replace=False)

    scores, models = [], {}
    for k in K_RANGE:
        km = MiniBatchKMeans(n_clusters=k, random_state=SEED,
                             batch_size=10_000, n_init=5).fit(X)
        sil = silhouette_score(X[sample], km.labels_[sample])
        scores.append([k, f"{km.inertia_:,.0f}", f"{sil:.3f}"])
        models[k] = (km, sil)
        log(f"  k={k}: silhouette {sil:.3f}")
    best_k = max(models, key=lambda k: models[k][1])
    best_sil = models[best_k][1]

    w("## 3. Clustering on the topological profile\n")
    w(f"Features: log(x + 1) of {', '.join(TOPO)}, standardised. "
      f"{int(mask.sum()):,} packages with a profile; those with every count "
      f"at zero are excluded, since as a single point they cannot be "
      f"clustered. k is fixed in advance as the highest silhouette, computed "
      f"on a random sample of {SIL_SAMPLE:,}.\n")
    w(md_table(["k", "inertia", "silhouette"], scores))

    if best_sil > 0.50:
        verdict = "reasonable structure"
    elif best_sil > 0.25:
        verdict = "weak structure"
    else:
        verdict = "no substantial structure"
    edge = " It sits at the edge of the range, so no natural k emerges." \
        if best_k == max(K_RANGE) else ""
    w(f"Best k = **{best_k}**, silhouette **{best_sil:.3f}**: {verdict}.{edge}\n")

    labels = models[best_k][0].labels_
    order = pd.Series(labels).value_counts().index
    rank = {c: i for i, c in enumerate(order)}
    df["role"] = -1
    df.loc[mask, "role"] = [rank[c] for c in labels]

    w("### Share of packages with each dependency type, by cluster\n")
    rows = []
    for r in range(best_k):
        g = df[df["role"] == r]
        cells = [f"{(g[c] > 0).mean() * 100:.0f}%" for c in TOPO]
        rows.append([r, f"{len(g):,}", *cells,
                     f"{g['excluded'].mean() * 100:.1f}%"])
    w(md_table(["cluster", "n"] + [f"{c} > 0" for c in TOPO] + ["excluded"],
               rows))

    w("### Clusters by decade stratum (row %)\n")
    ct = pd.crosstab(df.loc[mask, "role"], df.loc[mask, "stratum_decade"],
                     normalize="index") * 100
    cols = [s for s in STRATA if s in ct.columns]
    w(md_table(["cluster"] + cols,
               [[r] + [f"{ct.loc[r, s]:.1f}%" for s in cols] for r in ct.index]))

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    keep = ["package", "stratum_decade", "dangling_share", "fan_in_from_spam",
            *EXCLUSIONS, "excluded", "eligible", "role"]
    df[keep].to_parquet(OUT_TABLE, index=False)
    log(f"wrote {OUT_MD} and {OUT_TABLE}")


if __name__ == "__main__":
    main()