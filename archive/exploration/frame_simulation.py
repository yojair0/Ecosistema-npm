#!/usr/bin/env python3
"""
Cleaning simulation with the chosen criteria, and correlations of every
available variable with network position.

Unlike strata_correlations.py, which took the exclusions of pass 7b as one
block, this script lists each criterion explicitly, with its evidence, and
measures what each one contributes: for every criterion it recomputes the
correlations without it (ablation). A criterion that changes little can be
defended as harmless; one that changes a lot needs the strongest evidence.

It also tests one candidate criterion, small coordinated networks, because
the fan-in band 8-15 looked anomalous in the first simulation: younger
packages, fewer versions and many dependencies. The candidate is reported
with its own baseline, how often it appears before 2020, and it is not
applied unless switched on in CRITERIA.

Variables tested: every column available that is not built from the
targets themselves.
  - Metadata (pass 04): versions, maintainers, keywords, files, size, age,
    deprecated, GitHub link, scope, and days since modification. Pass 06
    discarded that last one because npm rewrote the date of 1.58 million
    packages; it is shown only for completeness.
  - Other dependency types (pass 03): development, peer and optional
    fan-in and fan-out. They are not cleaned of spam.
  - Network signals (pass 7b): same-family fan-in, missing dependencies,
    and the share of dependents with one version or with no dependents of
    their own, defined only for packages that have dependents.
Left out on purpose: creation year, which carries the same information as
age, and the components of the exclusion rules (burst spread, recent
dependents, born-with share), which would correlate with fan-in by
construction.

Targets: clean out-of-scope fan-in, and fan-out counting only dependencies
that exist. Cells give Spearman's rho with the half-width of its 95%
interval; with millions of packages every correlation is significant, so
the size is what matters.

Input : data/07_strata_analysis/signals.parquet
        data/06_profile_analysis/profile_table.parquet
        analysis_rerun/indicators.parquet          (optional)
Output: data/07_strata_analysis/simulation/simulation_report.md
        data/07_strata_analysis/simulation/*.csv
        data/07_strata_analysis/simulation/figures/*.png
"""
import os
import time
import warnings

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

SIGNALS = "data/07_strata_analysis/signals.parquet"
PROFILE = "data/06_profile_analysis/profile_table.parquet"
INDICATORS = "analysis_rerun/indicators.parquet"
OUT = "data/07_strata_analysis/simulation"
FIGURES = f"{OUT}/figures"

# Criteria: applied?, evidence. Switch one off to see the frame without it.
CRITERIA = {
    "security_placeholder": (True, "npm leaves an empty package when it removes malware; "
                                   "80% have no maintainers"),
    "types_only": (True, "type declarations only, no JavaScript to analyze"),
    "platform_binary": (True, "compiled programs for one system; same result as Viki's pattern "
                              "on the common format"),
    "spam_declarer": (True, "among packages declaring 50 or more, almost none between 10% and "
                            "90% missing; the count moves 9% when the threshold moves"),
    "spam_propagated": (True, "more than half of its fan-in comes from spam declarers; "
                              "kept from pass 07"),
    "coordinated_core": (True, "pattern in 1.5% of packages created before 2020 against 81% "
                               "in 2024; 97% created in 2024"),
    "colluded_dependent": (True, "95% also flagged by Viki's identical-dependency indicator; "
                                 "99.5% created in 2024"),
    "under_one_year": (True, "a package needs time to be adopted, and the rules on dependents "
                             "need a year to judge"),
    "viki_bursts": (False, "Viki's scope bursts and identical dependency lists; no effect on "
                           "correlations in the first simulation"),
    "small_network": (False, "candidate: 10 to 19 dependents in one burst, born with the "
                             "package, 80% or more of them with one version"),
}
SMALL_MIN, SMALL_MAX, SMALL_ONE_VERSION = 10, 19, 0.8

STRATA = ["0a isolated", "0b consumer", "1-9", "10-99", "100-999", ">=1000"]
STRATA_ES = {"0a isolated": "0a aislados", "0b consumer": "0b consumidores",
             ">=1000": "1,000 o más"}
META = ["n_versions", "n_maintainers", "n_keywords", "file_count", "unpacked", "age_days",
        "deprecated", "has_github", "scoped", "days_since_mod"]
DEPTYPES = ["fan_out", "fan_out_dev", "fan_out_peer", "fan_out_opt",
            "fan_in_dev", "fan_in_peer", "fan_in_opt"]
NETWORK = ["fan_in_same_scope", "deps_missing", "dep_one_version_share", "dep_fan_in_zero_share"]
BINARY_VARS = ["deprecated", "has_github", "scoped"]
SHARE_VARS = ["dep_one_version_share", "dep_fan_in_zero_share"]
LABELS_ES = {"n_versions": "Versiones", "n_maintainers": "Mantenedores", "n_keywords": "Keywords",
             "file_count": "Archivos", "unpacked": "Tamaño", "age_days": "Edad",
             "deprecated": "Deprecado", "has_github": "Enlaza a GitHub", "scoped": "Tiene scope",
             "days_since_mod": "Días desde modificación", "fan_out": "Fan-Out",
             "fan_out_dev": "Fan-Out desarrollo", "fan_out_peer": "Fan-Out peer",
             "fan_out_opt": "Fan-Out opcional", "fan_in_dev": "Fan-In desarrollo",
             "fan_in_peer": "Fan-In peer", "fan_in_opt": "Fan-In opcional",
             "fan_in_same_scope": "Fan-In misma familia", "deps_missing": "Dependencias inexistentes",
             "dep_one_version_share": "% dependientes de 1 versión",
             "dep_fan_in_zero_share": "% dependientes sin dependientes"}
MAX_RHO, MAX_CHANGE = 0.30, 0.05
GRADIENT_EDGES = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, np.inf]
GRADIENT_LABELS = ["0", "1", "2-3", "4-7", "8-15", "16-31", "32-63", "64-127",
                   "128-255", "256-511", "512-1023", "1024+"]
PERIOD_EDGES = [2010, 2019, 2023, 2024, 2026]
PERIODS = ["2011-2019", "2020-2023", "2024", "2025-2026"]

T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.0f}s] {msg}", flush=True)


def as_float(series):
    if series.dtype == object:
        series = series.map({True: 1.0, False: 0.0, "True": 1.0, "False": 0.0})
    return pd.to_numeric(series, errors="coerce").to_numpy(dtype=float, na_value=np.nan)


def spearman(x, y):
    """Spearman's rho on pairwise complete cases, with a 95% interval."""
    m = np.isfinite(x) & np.isfinite(y)
    n = int(m.sum())
    if n < 10:
        return np.nan, np.nan, np.nan, n
    rx = pd.Series(x[m]).rank().to_numpy()
    ry = pd.Series(y[m]).rank().to_numpy()
    if rx.std() == 0 or ry.std() == 0:
        return np.nan, np.nan, np.nan, n
    rho = float(np.corrcoef(rx, ry)[0, 1])
    se = 1.06 / np.sqrt(max(n - 3, 1))
    z = np.arctanh(np.clip(rho, -0.999999, 0.999999))
    return rho, float(np.tanh(z - 1.96 * se)), float(np.tanh(z + 1.96 * se)), n


def cell(rho, lo, hi, n=None):
    if not np.isfinite(rho):
        return "-"
    text = f"{rho:+.3f} ±{(hi - lo) / 2:.3f}"
    return f"{text} (n={n:,})" if n is not None else text


def md_table(header, rows):
    out = ["| " + " | ".join(str(h) for h in header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def fmt(x):
    return f"{x:,.0f}" if float(x).is_integer() or abs(x) >= 100 else f"{x:,.2f}"


def summarize(v, mask, variables):
    """Median [25th-75th] for counts, % for yes/no and shares.
    Age in years, size in KB."""
    row = {"packages": int(mask.sum())}
    for name in variables:
        x = v[name][mask]
        x = x[np.isfinite(x)]
        if not len(x):
            row[name] = "-"
        elif name in BINARY_VARS:
            row[name] = f"{x.mean() * 100:.1f}%"
        else:
            scale = 365 if name == "age_days" else 1024 if name == "unpacked" else 1
            q = np.percentile(x, [50, 25, 75]) / scale
            if name in SHARE_VARS:
                row[name] = f"{q[0] * 100:.0f}% [{q[1] * 100:.0f}-{q[2] * 100:.0f}]"
            else:
                row[name] = f"{fmt(q[0])} [{fmt(q[1])}-{fmt(q[2])}]"
    return row


def main():
    warnings.filterwarnings("ignore", category=RuntimeWarning)   # empty groups give NaN
    os.makedirs(FIGURES, exist_ok=True)

    log("loading signals and profile")
    s = pd.read_parquet(SIGNALS, columns=[
        "name", "security_placeholder", "types_only", "platform_binary", "spam_declarer",
        "spam_propagated", "coordinated_core", "colluded_dependent", "old_enough",
        "stratum_clean_out_of_scope", "fan_in_raw", "fan_in_clean_out_of_scope",
        "fan_in_same_scope", "deps_declared", "deps_missing", "dep_dated", "dep_span_p05_p95",
        "dep_recent_365", "burst_lag_days", "dep_one_version_share", "dep_fan_in_zero_share"])
    available = set(pq.read_schema(PROFILE).names)
    wanted = [c for c in META + DEPTYPES + ["created_year"] if c in available and c != "fan_out"]
    p = pd.read_parquet(PROFILE, columns=["name"] + wanted)
    d0 = s.merge(p.drop_duplicates("name"), on="name", how="left")
    n = len(d0)

    v = {c: as_float(d0[c]) for c in wanted}
    v["fan_out"] = (d0["deps_declared"] - d0["deps_missing"]).to_numpy(dtype=float)
    fi_raw = d0["fan_in_raw"].to_numpy(dtype=float)
    fi_clean = d0["fan_in_clean_out_of_scope"].to_numpy(dtype=float)
    v["fan_in_same_scope"] = d0["fan_in_same_scope"].to_numpy(dtype=float)
    v["deps_missing"] = d0["deps_missing"].to_numpy(dtype=float)
    for c in SHARE_VARS:
        v[c] = np.where(fi_raw > 0, d0[c].to_numpy(dtype=float), np.nan)
    variables = [c for c in META + DEPTYPES + NETWORK if c in v]
    skipped = [c for c in META + DEPTYPES + NETWORK if c not in v]
    group = {c: ("metadata" if c in META else "dependency types" if c in DEPTYPES
                 else "network signals") for c in variables}
    has_profile = np.isfinite(v["age_days"])
    year = v.get("created_year", np.full(n, np.nan))
    period = np.asarray(pd.cut(year, PERIOD_EDGES, labels=PERIODS).astype(object))
    stratum = d0["stratum_clean_out_of_scope"].to_numpy(dtype=object)
    old_enough = d0["old_enough"].to_numpy(dtype=bool)

    # ------------------------------------------------------------ criteria
    flag = {c: d0[c].to_numpy(dtype=bool) for c in
            ["security_placeholder", "types_only", "platform_binary", "spam_declarer",
             "spam_propagated", "coordinated_core", "colluded_dependent"]}
    flag["under_one_year"] = ~old_enough
    if os.path.exists(INDICATORS):
        ind = pd.read_parquet(INDICATORS)
        ind["name"] = ind["name"].astype(str).str.strip().str.lower()
        cols = [c for c in ind.columns if c.startswith(("ind_sb_", "ind_dgb_"))]
        viki = (ind.drop_duplicates("name").set_index("name")[cols]
                   .astype("boolean").fillna(False).any(axis=1))
        flag["viki_bursts"] = d0["name"].map(viki).fillna(False).to_numpy(dtype=bool)
    dep_dated = d0["dep_dated"].to_numpy(dtype=float)
    span = d0["dep_span_p05_p95"].to_numpy(dtype=float)
    recent_share = d0["dep_recent_365"].to_numpy(dtype=float) / np.maximum(dep_dated, 1)
    lag = d0["burst_lag_days"].to_numpy(dtype=float)
    one_version_dependents = d0["dep_one_version_share"].to_numpy(dtype=float)
    small_population = (dep_dated >= SMALL_MIN) & (dep_dated <= SMALL_MAX) & old_enough
    flag["small_network"] = (small_population & (span >= 0) & (span <= 120)
                             & (recent_share <= 0.005) & (lag < 365)
                             & (one_version_dependents >= SMALL_ONE_VERSION))

    applied = [c for c, (on, _) in CRITERIA.items() if on and c in flag]
    tested = [c for c, (on, _) in CRITERIA.items() if not on and c in flag]

    def frame_mask(criteria):
        m = has_profile.copy()
        for c in criteria:
            m &= ~flag[c]
        return m

    frame = frame_mask(applied)
    crit_rows = []
    for c, (on, evidence) in CRITERIA.items():
        if c not in flag:
            crit_rows.append([c, "not available", "-", "-", evidence])
            continue
        others = [x for x in applied if x != c]
        alone = has_profile & flag[c]
        for x in others:
            alone &= ~flag[x]
        crit_rows.append([c, "applied" if on else "tested only",
                          f"{int((has_profile & flag[c]).sum()):,}",
                          f"{int(alone.sum()):,}", evidence])

    strata_rows = [[s_, f"{int((has_profile & (stratum == s_)).sum()):,}",
                    f"{int((frame & (stratum == s_)).sum()):,}"] for s_ in STRATA]

    # --------------------------------------------- global correlations
    log("global correlations and ablation (several minutes)")
    variants = {"A: all packages, raw fan-in": (has_profile, fi_raw),
                "A1: without rule exclusions, raw fan-in":
                    (frame_mask([c for c in applied if c != "under_one_year"]), fi_raw),
                "F: final frame, clean fan-in": (frame, fi_clean)}
    for c in applied:
        variants[f"F without {c}"] = (frame_mask([x for x in applied if x != c]), fi_clean)
    for c in tested:
        variants[f"F plus {c}"] = (frame_mask(applied + [c]), fi_clean)
    results = {k: {x: spearman(v[x][m], t[m]) for x in variables} for k, (m, t) in variants.items()}
    pd.DataFrame([{"variant": k, "variable": x, "rho": r[0], "ci_low": r[1], "ci_high": r[2],
                   "n": r[3]} for k, res in results.items() for x, r in res.items()]) \
        .to_csv(f"{OUT}/global_correlations.csv", index=False)
    kA, kA1, kF = list(variants)[:3]
    global_rows = [[x, group[x]] + [cell(*results[k][x][:3]) for k in (kA, kA1, kF)]
                   for x in variables]
    pre_rows = []
    for x in [c for c in META if c in variables and c != "days_since_mod"]:
        a, a1 = results[kA][x][0], results[kA1][x][0]
        ok = abs(a1) <= MAX_RHO and abs(a1 - a) <= MAX_CHANGE
        pre_rows.append([x, f"{a:+.3f}", f"{a1:+.3f}", f"{a1 - a:+.3f}", "holds" if ok else "FAILS"])

    def deltas(key):
        return {x: results[key][x][0] - results[kF][x][0] for x in variables}

    key_vars = [x for x in ["n_versions", "age_days", "file_count", "has_github", "fan_in_dev"]
                if x in variables]
    abl_rows, abl_max = [], {}
    for k in [k for k in variants if k.startswith(("F without", "F plus"))]:
        dl = deltas(k)
        finite = {x: abs(val) for x, val in dl.items() if np.isfinite(val)}
        top = max(finite, key=finite.get) if finite else "-"
        abl_max[k] = finite.get(top, 0.0)
        packages = int(variants[k][0].sum()) - int(frame.sum())
        abl_rows.append([k, f"{packages:+,}"] + [f"{dl[x]:+.3f}" for x in key_vars]
                        + [f"{top} ({dl[top]:+.3f})" if top != "-" else "-"])

    # --------------------------------------------- candidate baseline
    base_rows = []
    for per in PERIODS:
        m = has_profile & small_population & (period == per)
        k = int(m.sum())
        f = int((m & flag["small_network"]).sum())
        base_rows.append([per, f"{k:,}", f"{f:,}", f"{f / k * 100:.1f}%" if k else "-"])

    # --------------------------------------------- correlations by stratum
    log("correlations by stratum")
    strat = []
    for target_name, target in [("fan_in", fi_clean), ("fan_out", v["fan_out"])]:
        for st in STRATA:
            m = frame & (stratum == st)
            for x in variables:
                if x == target_name:
                    continue
                r = spearman(v[x][m], target[m])
                strat.append({"target": target_name, "stratum": st, "variable": x,
                              "rho": r[0], "ci_low": r[1], "ci_high": r[2], "n": r[3]})
    strat = pd.DataFrame(strat)
    strat.to_csv(f"{OUT}/stratum_correlations.csv", index=False)

    def strat_table(target_name):
        rows = []
        for x in variables:
            if x == target_name:
                continue
            row = [x]
            for st in STRATA:
                r = strat[(strat.target == target_name) & (strat.stratum == st)
                          & (strat.variable == x)].iloc[0]
                row.append(cell(r.rho, r.ci_low, r.ci_high, int(r.n)))
            rows.append(row)
        return md_table(["Variable"] + STRATA, rows)

    # --------------------------------------------- profiles and gradient
    log("profiles, gradient and band check")
    part1 = [x for x in variables if x in META or x in DEPTYPES]
    part2 = [x for x in variables if x in NETWORK]
    prof = [{"stratum": st, **summarize(v, frame & (stratum == st), variables)} for st in STRATA]
    pd.DataFrame(prof).to_csv(f"{OUT}/stratum_profile.csv", index=False)
    bins = np.asarray(pd.cut(fi_clean, GRADIENT_EDGES, right=False,
                             labels=GRADIENT_LABELS).astype(object))
    grad = [{"fan_in": b, **summarize(v, frame & (bins == b), variables)} for b in GRADIENT_LABELS]
    pd.DataFrame(grad).to_csv(f"{OUT}/gradient.csv", index=False)

    def wide(rows, key, cols):
        return md_table([key, "Packages"] + cols,
                        [[r[key], f"{r['packages']:,}"] + [r[c] for c in cols] for r in rows])

    band_rows, band_periods = [], {}
    for b in ["4-7", "8-15", "16-31"]:
        m = frame & (bins == b)
        k = int(m.sum())
        shares = {per: (m & (period == per)).sum() / max(k, 1) * 100 for per in PERIODS}
        band_periods[b] = shares
        nv = v["n_versions"][m]
        fo = v["fan_out"][m]
        row = [b, f"{k:,}"] + [f"{shares[per]:.1f}%" for per in PERIODS] + [
            f"{np.mean(nv == 1) * 100:.1f}%" if k else "-",
            f"{np.nanpercentile(fo, 75):.0f}" if k else "-",
            f"{(m & flag['small_network']).sum() / max(k, 1) * 100:.1f}%"]
        if "viki_bursts" in flag:
            row.append(f"{(m & flag['viki_bursts']).sum() / max(k, 1) * 100:.1f}%")
        band_rows.append(row)
    band_header = (["Fan-in", "Packages"] + [f"Created {p_}" for p_ in PERIODS]
                   + ["One version", "Fan-out p75", "Small-network candidate"]
                   + (["Viki's bursts"] if "viki_bursts" in flag else []))

    # --------------------------------------------- figures
    log("drawing figures")
    figures = []
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        def save(fig, name):
            fig.tight_layout()
            fig.savefig(f"{FIGURES}/{name}", dpi=150)
            plt.close(fig)
            figures.append(f"{FIGURES}/{name}")

        names = list(abl_max)
        fig, ax = plt.subplots(figsize=(9, 0.5 * len(names) + 1.5))
        ax.barh([k.replace("F without ", "sin ").replace("F plus ", "con ") for k in names],
                [abl_max[k] for k in names])
        ax.axvline(MAX_CHANGE, color="gray", linestyle="--", linewidth=1)
        ax.set_xlabel("Mayor cambio en una correlación con el Fan-In")
        ax.set_title("Cuánto cambia cada criterio las conclusiones")
        save(fig, "fig_s1_ablation.png")

        fi = strat[strat.target == "fan_in"].pivot(index="variable", columns="stratum", values="rho")
        fi = fi.reindex(index=variables, columns=STRATA[2:])
        fig, ax = plt.subplots(figsize=(8, 0.4 * len(variables) + 2))
        im = ax.imshow(fi.to_numpy(dtype=float), cmap="RdBu_r", vmin=-0.6, vmax=0.6, aspect="auto")
        ax.set_xticks(range(len(fi.columns)), [STRATA_ES.get(c, c) for c in fi.columns])
        ax.set_yticks(range(len(fi.index)), [LABELS_ES.get(x, x) for x in fi.index])
        for i in range(fi.shape[0]):
            for j in range(fi.shape[1]):
                val = fi.iat[i, j]
                if np.isfinite(val):
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7)
        fig.colorbar(im, ax=ax, label="rho de Spearman")
        ax.set_title("Correlación con el Fan-In dentro de cada estrato")
        save(fig, "fig_s2_within_stratum.png")

        fig, ax = plt.subplots(figsize=(7, 4))
        bottom = np.zeros(3)
        for per in PERIODS:
            values = np.array([band_periods[b][per] for b in ["4-7", "8-15", "16-31"]])
            ax.bar(["4-7", "8-15", "16-31"], values, bottom=bottom, label=f"Creados {per}")
            bottom += values
        ax.set_ylabel("% de los paquetes del tramo")
        ax.set_xlabel("Fan-In limpio")
        ax.set_title("¿Cuándo se crearon los paquetes de cada tramo?")
        ax.legend(fontsize=8)
        save(fig, "fig_s3_band_check.png")
    except ImportError:
        log("matplotlib is not installed, skipping figures")

    # --------------------------------------------- report
    log("writing report")
    lines = [
        "# Cleaning simulation with explicit criteria\n",
        f"Generated {time.strftime('%Y-%m-%d %H:%M')} over {n:,} packages; "
        f"{int(has_profile.sum()):,} have a profile.\n",
        "Cells give Spearman's rho ± half-width of its 95% interval. Reference: "
        "|rho| 0.1 small, 0.3 medium, 0.5 large.\n",
        (f"Variables not found and skipped: {', '.join(skipped)}.\n" if skipped else ""),
        "## Criteria\n",
        "Flagged: packages with a profile that the criterion marks. Only this criterion: "
        "those no other applied criterion marks, which is what switching it off brings back.\n",
        md_table(["Criterion", "Status", "Flagged", "Only this criterion", "Evidence"], crit_rows),
        "## Frame by stratum\n",
        md_table(["Stratum", "Packages with profile", "In the frame"], strata_rows),
        f"Frame total: {int(frame.sum()):,} packages.\n",
        "## 1. Global correlation with fan-in, every variable\n",
        md_table(["Variable", "Group", kA, kA1, kF], global_rows),
        f"### Criterion fixed beforehand (A against A1): |rho| <= {MAX_RHO} and change <= {MAX_CHANGE}\n",
        md_table(["Variable", "A", "A1", "Change", "Result"], pre_rows),
        "## 2. What each criterion contributes (ablation)\n",
        "Each row recomputes the frame without one applied criterion, or with one tested "
        "criterion added, and gives the change in the correlation with fan-in against F. "
        f"Changes under {MAX_CHANGE} do not alter any conclusion.\n",
        md_table(["Variant", "Packages vs F"] + key_vars + ["Largest change"], abl_rows),
        "## 3. Candidate criterion: small coordinated networks\n",
        f"Packages at least one year old with {SMALL_MIN} to {SMALL_MAX} dated dependents from "
        "other families. Flagged: one burst of 120 days or less, none in the last year, born "
        f"with the package, and {SMALL_ONE_VERSION:.0%} or more of its dependents with one "
        "version. Before 2020 there were no known campaigns, so that row approximates how "
        "often organic packages meet it by chance.\n",
        md_table(["Created", "Packages with 10-19 dependents", "Flagged", "Share"], base_rows),
        "## 4. The fan-in bands around 8-15 (frame)\n",
        md_table(band_header, band_rows),
        "## 5. Correlations within each stratum (frame)\n",
        "A dash means the target does not vary in that stratum, as fan-in in 0a and 0b.\n",
        "### With fan-in\n",
        strat_table("fan_in"),
        "### With fan-out\n",
        strat_table("fan_out"),
        "## 6. Profile of each stratum (frame)\n",
        "Median [25th-75th percentile]; % for yes/no variables and shares; age in years; "
        "size in KB.\n",
        wide(prof, "stratum", part1),
        wide(prof, "stratum", part2),
        "## 7. Gradient along clean fan-in (frame)\n",
        "Bins that double each time. Same units as the profile.\n",
        wide(grad, "fan_in", part1),
        wide(grad, "fan_in", part2),
        "## Figures\n",
        "\n".join(f"- `{f}`" for f in figures) or "- not generated",
    ]
    with open(f"{OUT}/simulation_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log(f"done: {OUT}/simulation_report.md")


if __name__ == "__main__":
    main()