#!/usr/bin/env python3
"""
Correlations between package metadata and network position, by stratum,
after removing the packages that the exclusion rules flag.

Exploratory: the exclusion criteria are not final until the professor
approves them. The script answers three questions:

  1. Does removing excluded packages change the global correlations of the
     profile analysis (pass 06)? Criterion fixed beforehand: the conclusion
     holds if no profile variable exceeds |rho| = 0.30 and no correlation
     changes by more than 0.05.
  2. Within each stratum, which variables relate to fan-in and fan-out?
  3. Along the whole fan-in range, do the variables change gradually or in
     steps? A gradual change supports strata by order of magnitude as a
     convention, since there are no natural boundaries to find.

Exclusions are those of pass 7b (version 5): security placeholders, @types,
platform binaries, spam declarers, spam propagated, coordinated cores and
colluded dependents. Burst victims stay, with their burst left out of their
fan-in. Viki's metadata indicators (scope bursts, identical dependency
lists) are not applied; when analysis_rerun/indicators.parquet exists they
are tested as a sensitivity variant.

Within a stratum the range of fan-in is narrow, which shrinks correlations
(range restriction): a low correlation inside a stratum does not mean the
variable is unrelated to position across strata. Section 3 covers that.
With millions of packages every correlation is statistically significant,
so the report gives effect sizes with 95% intervals instead of p-values.

Fan-out here counts only dependencies that exist, so that fan-in and
fan-out describe the same network.

Input : data/07_strata_analysis/signals.parquet
        data/06_profile_analysis/profile_table.parquet
        analysis_rerun/indicators.parquet          (optional)
Output: data/07_strata_analysis/correlations/correlations_report.md
        data/07_strata_analysis/correlations/*.csv
        data/07_strata_analysis/correlations/figures/*.png
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
OUT = "data/07_strata_analysis/correlations"
FIGURES = f"{OUT}/figures"

STRATA = ["0a isolated", "0b consumer", "1-9", "10-99", "100-999", ">=1000"]
STRATA_ES = {"0a isolated": "0a aislados", "0b consumer": "0b consumidores",
             ">=1000": "1,000 o más"}
PROFILE_VARS = ["n_versions", "n_maintainers", "n_keywords", "file_count", "unpacked",
                "age_days", "deprecated", "has_github", "scoped"]
NETWORK_VARS = ["fan_in_dev", "fan_in_peer", "fan_out"]
BINARY_VARS = ["deprecated", "has_github", "scoped"]
LABELS_ES = {"n_versions": "Versiones", "n_maintainers": "Mantenedores",
             "n_keywords": "Keywords", "file_count": "Archivos", "unpacked": "Tamaño",
             "age_days": "Edad", "deprecated": "Deprecado", "has_github": "Enlaza a GitHub",
             "scoped": "Tiene scope", "fan_in_dev": "Fan-In de desarrollo",
             "fan_in_peer": "Fan-In peer", "fan_out": "Fan-Out"}
MAX_RHO = 0.30            # fixed beforehand: no profile variable above this
MAX_CHANGE = 0.05         # fixed beforehand: no correlation moves more than this
VARIANT_ES = {"A": "A: todo, Fan-In bruto", "A1": "A1: sin excluidos, Fan-In bruto",
              "B": "B: sin excluidos, Fan-In limpio", "C": "C: marco de muestreo",
              "D": "D: marco sin ráfagas de Viki"}
GRADIENT_EDGES = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, np.inf]
GRADIENT_LABELS = ["0", "1", "2-3", "4-7", "8-15", "16-31", "32-63", "64-127",
                   "128-255", "256-511", "512-1023", "1024+"]

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
    se = 1.06 / np.sqrt(max(n - 3, 1))            # Fieller et al. for Spearman
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
    return f"{x:,.0f}" if float(x).is_integer() or abs(x) >= 100 else f"{x:,.1f}"


def summarize(d, mask, variables):
    """Medians with interquartile range for counts, percentages for yes/no.
    Age in years and unpacked size in KB."""
    row = {"packages": int(mask.sum())}
    for v in variables:
        x = d[v][mask]
        x = x[np.isfinite(x)]
        if not len(x):
            row[v] = "-"
        elif v in BINARY_VARS:
            row[v] = f"{x.mean() * 100:.1f}%"
        else:
            scale = 365 if v == "age_days" else 1024 if v == "unpacked" else 1
            q = np.percentile(x, [50, 25, 75]) / scale
            row[v] = f"{fmt(q[0])} [{fmt(q[1])}-{fmt(q[2])}]"
    return row


def main():
    warnings.filterwarnings("ignore", category=RuntimeWarning)   # empty bins give NaN
    os.makedirs(FIGURES, exist_ok=True)
    log("loading signals and profile")
    s = pd.read_parquet(SIGNALS, columns=[
        "name", "excluded_any", "eligible", "stratum_raw", "stratum_clean_out_of_scope",
        "fan_in_raw", "fan_in_clean_out_of_scope", "deps_declared", "deps_missing"])
    available = set(pq.read_schema(PROFILE).names)
    wanted = [v for v in PROFILE_VARS + ["fan_in_dev", "fan_in_peer"] if v in available]
    missing_cols = sorted(set(PROFILE_VARS + ["fan_in_dev", "fan_in_peer"]) - set(wanted))
    p = pd.read_parquet(PROFILE, columns=["name"] + wanted)
    d0 = s.merge(p.drop_duplicates("name"), on="name", how="left")
    n = len(d0)

    d = {v: as_float(d0[v]) for v in wanted}
    d["fan_out"] = (d0["deps_declared"] - d0["deps_missing"]).to_numpy(dtype=float)
    variables = [v for v in PROFILE_VARS + NETWORK_VARS if v in d]
    profile_vars = [v for v in PROFILE_VARS if v in d]
    fi_raw = d0["fan_in_raw"].to_numpy(dtype=float)
    fi_clean = d0["fan_in_clean_out_of_scope"].to_numpy(dtype=float)
    excluded = d0["excluded_any"].to_numpy(dtype=bool)
    eligible = d0["eligible"].to_numpy(dtype=bool)
    has_profile = np.isfinite(d["age_days"]) if "age_days" in d else np.ones(n, bool)
    stratum = d0["stratum_clean_out_of_scope"].to_numpy(dtype=object)
    stratum_raw = d0["stratum_raw"].to_numpy(dtype=object)

    variants = {
        "A all, raw fan-in": (has_profile, fi_raw),
        "A1 without excluded, raw fan-in": (has_profile & ~excluded, fi_raw),
        "B without excluded, clean fan-in": (has_profile & ~excluded, fi_clean),
        "C frame (B + one year), clean fan-in": (has_profile & eligible, fi_clean),
    }
    if os.path.exists(INDICATORS):
        ind = pd.read_parquet(INDICATORS)
        ind["name"] = ind["name"].astype(str).str.strip().str.lower()
        cols = [c for c in ind.columns if c.startswith(("ind_sb_", "ind_dgb_"))]
        viki = ind.drop_duplicates("name").set_index("name")[cols].astype("boolean") \
                  .fillna(False).any(axis=1)
        viki_flag = d0["name"].map(viki).fillna(False).to_numpy(dtype=bool)
        variants["D frame minus Viki's bursts, clean fan-in"] = (
            has_profile & eligible & ~viki_flag, fi_clean)
    else:
        viki_flag = None

    # --------------------------------------------- 1. global correlations
    log("global correlations")
    rows = []
    for v in variables:
        row = {"variable": v}
        for name, (mask, target) in variants.items():
            rho, lo, hi, k = spearman(d[v][mask], target[mask])
            row[name] = (rho, lo, hi, k)
        rows.append(row)
    keys = list(variants)
    global_csv = pd.DataFrame([{"variable": r["variable"], "variant": k, "rho": r[k][0],
                                "ci_low": r[k][1], "ci_high": r[k][2], "n": r[k][3]}
                               for r in rows for k in keys])
    global_csv.to_csv(f"{OUT}/global_correlations.csv", index=False)
    pre_rows = []
    for r in rows:
        if r["variable"] not in profile_vars:
            continue
        a, a1 = r[keys[0]][0], r[keys[1]][0]
        change = a1 - a
        ok = abs(a1) <= MAX_RHO and abs(change) <= MAX_CHANGE
        pre_rows.append([r["variable"], f"{a:+.3f}", f"{a1:+.3f}", f"{change:+.3f}",
                         "holds" if ok else "FAILS"])

    # --------------------------------------------- 2. correlations by stratum
    log("correlations by stratum")
    frame = has_profile & eligible
    strat_rows = []
    for target_name, target in [("fan_in", fi_clean), ("fan_out", d["fan_out"])]:
        for st in STRATA:
            m = frame & (stratum == st)
            for v in variables:
                if v == target_name:
                    continue
                rho, lo, hi, k = spearman(d[v][m], target[m])
                strat_rows.append({"target": target_name, "stratum": st, "variable": v,
                                   "rho": rho, "ci_low": lo, "ci_high": hi, "n": k})
    strat = pd.DataFrame(strat_rows)
    strat.to_csv(f"{OUT}/stratum_correlations.csv", index=False)

    # --------------------------------------------- profile by stratum
    profile_frame = pd.DataFrame([{"stratum": st, **summarize(d, frame & (stratum == st), variables)}
                                  for st in STRATA])
    profile_frame.to_csv(f"{OUT}/stratum_profile.csv", index=False)
    comp_rows = []
    for st in STRATA:
        for label, mask in [("raw population", has_profile & (stratum_raw == st)),
                            ("frame", frame & (stratum == st))]:
            nv = d["n_versions"][mask]
            fc = d["file_count"][mask] if "file_count" in d else np.array([np.nan])
            fc = fc[np.isfinite(fc)]
            age = d["age_days"][mask]
            comp_rows.append({
                "stratum": st, "set": label, "packages": int(mask.sum()),
                "pct_one_version": round(float(np.mean(nv == 1) * 100), 1) if mask.any() else np.nan,
                "median_files": round(float(np.median(fc)), 1) if len(fc) else np.nan,
                "median_age_years": round(float(np.nanmedian(age) / 365), 1) if mask.any() else np.nan,
                "pct_deprecated": (round(float(np.nanmean(d["deprecated"][mask]) * 100), 1)
                                   if "deprecated" in d and mask.any() else np.nan)})
    composition = pd.DataFrame(comp_rows)
    composition.to_csv(f"{OUT}/strata_composition.csv", index=False)

    # --------------------------------------------- 3. gradient along fan-in
    log("gradient along fan-in")
    bins = pd.cut(fi_clean, GRADIENT_EDGES, right=False, labels=GRADIENT_LABELS)
    bins = np.asarray(bins.astype(object))
    grad = pd.DataFrame([{"fan_in": b, **summarize(d, frame & (bins == b), variables)}
                         for b in GRADIENT_LABELS])
    grad.to_csv(f"{OUT}/gradient.csv", index=False)
    grad_numeric = pd.DataFrame([{
        "fan_in": b,
        **{v: (np.nanmean(d[v][frame & (bins == b)]) * 100 if v in BINARY_VARS
               else np.nanmedian(d[v][frame & (bins == b)]))
           for v in variables}} for b in GRADIENT_LABELS])

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

        fi = strat[strat["target"] == "fan_in"].pivot(index="variable", columns="stratum",
                                                         values="rho")
        fi = fi.reindex(index=variables, columns=STRATA[2:])
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(fi.to_numpy(dtype=float), cmap="RdBu_r", vmin=-0.5, vmax=0.5)
        ax.set_xticks(range(len(fi.columns)), [STRATA_ES.get(c, c) for c in fi.columns])
        ax.set_yticks(range(len(fi.index)), [LABELS_ES[v] for v in fi.index])
        for i in range(fi.shape[0]):
            for j in range(fi.shape[1]):
                val = fi.iat[i, j]
                if np.isfinite(val):
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8)
        fig.colorbar(im, ax=ax, label="rho de Spearman")
        ax.set_title("Correlación con el Fan-In dentro de cada estrato")
        save(fig, "fig_c1_within_stratum.png")

        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(variables))
        width = 0.8 / len(keys)
        for i, k in enumerate(keys):
            values = [r[k][0] for r in rows]
            ax.bar(x + (i - (len(keys) - 1) / 2) * width, values, width,
                   label=VARIANT_ES[k.split()[0]])
        ax.axhline(MAX_RHO, color="gray", linestyle="--", linewidth=1)
        ax.axhline(-MAX_RHO, color="gray", linestyle="--", linewidth=1)
        ax.set_xticks(x, [LABELS_ES[v] for v in variables], rotation=30, ha="right")
        ax.set_ylabel("rho de Spearman con el Fan-In")
        ax.set_title("Correlación global con el Fan-In, antes y después de limpiar")
        ax.legend(fontsize=7)
        save(fig, "fig_c2_global_by_variant.png")

        show = [v for v in ["n_versions", "file_count", "n_maintainers", "deprecated"] if v in d]
        fig, axes = plt.subplots(1, len(show), figsize=(4 * len(show), 4))
        for ax, v in zip(np.atleast_1d(axes), show):
            ax.plot(range(len(GRADIENT_LABELS)), grad_numeric[v], marker="o")
            ax.set_xticks(range(len(GRADIENT_LABELS)), GRADIENT_LABELS, rotation=60, fontsize=7)
            ax.set_title(LABELS_ES[v] + (" (%)" if v in BINARY_VARS else " (mediana)"))
            ax.set_xlabel("Fan-In limpio")
        fig.suptitle("Cómo cambian las variables a lo largo del Fan-In")
        save(fig, "fig_c3_gradient.png")
    except ImportError:
        log("matplotlib is not installed, skipping figures")

    # --------------------------------------------- report
    log("writing report")
    variant_rows = [[k, f"{int(m.sum()):,}"] for k, (m, _) in variants.items()]
    lines = [
        "# Correlations by stratum after exclusions\n",
        f"Generated {time.strftime('%Y-%m-%d %H:%M')} over {n:,} packages.\n",
        "Cells show Spearman's rho ± half-width of its 95% interval. With these sample "
        "sizes every correlation is significant; read the size. Reference: |rho| 0.1 small, "
        "0.3 medium, 0.5 large.\n",
        (f"Profile columns not found and skipped: {', '.join(missing_cols)}.\n"
         if missing_cols else ""),
        "## Variants\n",
        md_table(["Variant", "Packages"], variant_rows),
        "- A replicates pass 06. A1 removes the excluded packages and keeps raw fan-in, "
        "which is the comparison fixed beforehand. B also cleans the fan-in. C adds the "
        "one-year minimum: it is the sampling frame.",
        ("- D also removes the packages Viki's scope-burst or identical-dependency "
         f"indicators flag: {int((has_profile & eligible & viki_flag).sum()):,} of the frame.\n"
         if viki_flag is not None else "- D not computed: indicators.parquet not found.\n"),
        "## 1. Global correlation with fan-in\n",
        md_table(["Variable"] + keys,
                 [[r["variable"]] + [cell(*r[k][:3]) for k in keys] for r in rows]),
        f"### Criterion fixed beforehand (A against A1): |rho| <= {MAX_RHO} and change <= {MAX_CHANGE}\n",
        md_table(["Variable", "A", "A1", "Change", "Result"], pre_rows),
        "## 2. Correlations within each stratum (frame)\n",
        "Strata by clean out-of-scope fan-in. A dash means the target does not vary in that "
        "stratum, as fan-in in strata 0a and 0b.\n",
        "### With fan-in\n",
        md_table(["Variable"] + STRATA,
                 [[v] + [cell(*strat[(strat.target == "fan_in") & (strat.stratum == st)
                                     & (strat.variable == v)][["rho", "ci_low", "ci_high", "n"]]
                               .iloc[0].tolist()[:3],
                              n=int(strat[(strat.target == "fan_in") & (strat.stratum == st)
                                          & (strat.variable == v)]["n"].iloc[0]))
                         for st in STRATA] for v in variables]),
        "### With fan-out\n",
        md_table(["Variable"] + STRATA,
                 [[v] + [cell(*strat[(strat.target == "fan_out") & (strat.stratum == st)
                                     & (strat.variable == v)][["rho", "ci_low", "ci_high"]]
                               .iloc[0].tolist(),
                              n=int(strat[(strat.target == "fan_out") & (strat.stratum == st)
                                          & (strat.variable == v)]["n"].iloc[0]))
                         for st in STRATA] for v in variables if v != "fan_out"]),
        "## Profile of each stratum (frame)\n",
        "Median [25th-75th percentile]; percentages for yes/no variables; age in years; "
        "unpacked size in KB.\n",
        md_table(["Stratum", "Packages"] + variables,
                 [[r["stratum"], f"{r['packages']:,}"] + [r[v] for v in variables]
                  for r in profile_frame.to_dict("records")]),
        "## What the exclusions changed in each stratum\n",
        "Raw population: strata by raw fan-in, every package. Frame: strata by clean "
        "fan-in, eligible packages only.\n",
        md_table(list(composition.columns), composition.astype(str).values.tolist()),
        "## 3. Gradient along clean fan-in (frame)\n",
        "Finer bins than the strata, doubling each time. Same units as the profile table.\n",
        md_table(["Fan-in", "Packages"] + variables,
                 [[r["fan_in"], f"{r['packages']:,}"] + [r[v] for v in variables]
                  for r in grad.to_dict("records")]),
        "## Figures\n",
        "\n".join(f"- `{f}`" for f in figures) or "- not generated",
    ]
    with open(f"{OUT}/correlations_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(x for x in lines if x is not None) + "\n")
    log(f"done: {OUT}/correlations_report.md")


if __name__ == "__main__":
    main()