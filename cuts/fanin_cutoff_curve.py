#!/usr/bin/env python3
"""
fanin_cutoff_curve.py -- How the correlations change as only the more used (or
the more dependent) packages are kept.

For each population, the packages are cut by a measure, Fan-In or Fan-Out,
from the widest group to the narrowest, and every correlation of the profile
with that measure is computed again within each group. Reading each curve:
  - it rises when the lower packages are dropped: those packages were noise;
  - it falls from the start: there was no noise, and cutting only loses packages;
  - it stays flat: the conclusion does not depend on the cut.

The cuts come from two sources, so that none is chosen to suit a result:
  - the deciles of the measure in each population (the top 50%, 40%... that
    the professor asked for); ties at low values can make several deciles
    fall on the same cut, and the report says so;
  - a scale of 1, 2, 3, 5, 10, 20, 50... (0 for Fan-Out), finer at the bottom,
    which includes the decade cuts 10, 100 and 1000 of the stratification.

Each population also gets xmin: the value where the long tail of the measure
begins, estimated from the data with the method of Clauset, Shalizi and Newman
(2009, SIAM Review): a discrete power law is fitted above each candidate, and
xmin is the candidate whose fit is closest to the data (smallest
Kolmogorov-Smirnov distance). xmin is added as one more cut, as a candidate
with a statistical basis. The bootstrap test of whether the tail is truly a
power law is not run: xmin is used only as a reference point.

Six populations, all of used packages (at least one dependent):
  g1_reg, g1_clean   G1, with families
  g2_reg, g2_clean   G2, only external links (external Fan-In and Fan-Out)
  g3_reg, g3_clean   G3, without families
  reg: Fan-In of the registry; clean: Fan-In counted only with dependents
  inside population A. Membership follows each Fan-In.

Run from the repository root, after 07_fanin_population.py and
check_fanin_clean.py:
    python presentation/fanin_cutoff_curve.py

Input : data/fanin_population/fanin_population.parquet
        data/exploration/fanin_clean/fanin_clean.parquet
          (G2 with the clean Fan-In needs the version of check_fanin_clean.py
          that writes fan_in_external_clean; without it, that population is skipped)
Output: data/presentation/fanin_cutoff_curve/
          curvas_fan_in.md, curvas_fan_out.md   every number: xmin, one table per population,
                                                one comparison per variable, a summary
          curvas.csv                            the same numbers in long format
          figures/                              one chart per population and measure
          run_metadata.json
"""
import json
import sys
import time
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import zeta
from scipy.stats import rankdata


def repo_root():
    for p in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (p / "data" / "07_inclusion_packages").is_dir():
            return p
    sys.exit("data/07_inclusion_packages not found: run from the repository root")


BASE = repo_root()
STUDY = BASE / "data" / "fanin_population" / "fanin_population.parquet"
CLEAN = BASE / "data" / "exploration" / "fanin_clean" / "fanin_clean.parquet"
OUT = BASE / "data" / "presentation" / "fanin_cutoff_curve"
SNAPSHOT_DATE = date(2026, 9, 18)
SCALE = {"fan_in": [1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000],
         "fan_out": [0, 1, 2, 3, 5, 10, 20, 50, 100]}
DECILES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
MIN_N = 2_000          # a cut that keeps fewer packages is left out
CHANGE = 0.05          # a change in ρ smaller than this, or than 3/sqrt(n), counts as flat
XMIN_MAX = 1_000       # xmin candidates: values up to this one...
XMIN_TAIL = 100        # ...that leave at least this many packages in the tail
PROFILE = [("n_versions", "Versiones"), ("age_years", "Edad"), ("n_maintainers", "Mantenedores"),
           ("has_github", "En GitHub"), ("n_keywords", "Palabras clave"),
           ("fan_in_dev", "Dependientes de desarrollo"), ("fan_out_dev", "Dependencias de desarrollo")]
OTHER = {"fan_in": ("fo", "Fan-Out"), "fan_out": ("fi", "Fan-In")}
MEASURE_NAME = {"fan_in": "Fan-In", "fan_out": "Fan-Out"}
COLORS = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2", "#a16207", "#6b7280"]
TEXT, SOFT = "#111827", "#6b7280"


# ── Formats (Spanish) ────────────────────────────────────────────────
def d_es(v, d=3):
    return "—" if pd.isna(v) else f"{v:.{d}f}".replace(".", ",")


def p_es(v):
    return f"{v:.1f}".replace(".", ",") + "%"


def n_es(v):
    return f"{int(v):,}".replace(",", ".")


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]) + "\n"


# ── Data ─────────────────────────────────────────────────────────────
def spearman(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    if m.sum() < 3:
        return np.nan
    rx, ry = rankdata(x[m]), rankdata(y[m])
    dx, dy = rx - rx.mean(), ry - ry.mean()
    den = np.sqrt((dx * dx).sum() * (dy * dy).sum())
    return float((dx * dy).sum() / den) if den > 0 else np.nan


def load():
    cols = ["name", "scope_size", "created_date", "fan_in", "fan_in_external", "fan_out",
            "fan_out_external", "fan_in_dev", "fan_out_dev", "n_versions", "n_maintainers",
            "n_keywords", "has_github"]
    df = pd.read_parquet(STUDY, columns=cols)
    df["age_years"] = (pd.Timestamp(SNAPSHOT_DATE) - pd.to_datetime(df["created_date"])).dt.days / 365.25
    df["has_github"] = df["has_github"].fillna(0).astype(bool).astype(np.int8)
    if not CLEAN.exists():
        sys.exit(f"{CLEAN} not found: run check_fanin_clean.py first")
    clean = pd.read_parquet(CLEAN)
    have = [c for c in ("fan_in_clean", "fan_in_external_clean") if c in clean.columns]
    df = df.merge(clean[["name"] + have], on="name", how="left")
    for c in have:
        df[c] = df[c].fillna(0).astype("int64")
    return df


def populations(df):
    """(key, title, rows, Fan-In column, Fan-Out column); members have Fan-In of 1 or more."""
    nofam = df["scope_size"] < 2
    pops = [("g1_reg", "G1, con familias, Fan-In del registro", df, "fan_in", "fan_out"),
            ("g1_clean", "G1, con familias, Fan-In limpio", df, "fan_in_clean", "fan_out"),
            ("g2_reg", "G2, solo vínculos externos, Fan-In del registro", df, "fan_in_external",
             "fan_out_external"),
            ("g2_clean", "G2, solo vínculos externos, Fan-In limpio", df, "fan_in_external_clean",
             "fan_out_external"),
            ("g3_reg", "G3, sin familias, Fan-In del registro", df[nofam], "fan_in", "fan_out"),
            ("g3_clean", "G3, sin familias, Fan-In limpio", df[nofam], "fan_in_clean", "fan_out")]
    out, skipped = [], []
    for key, title, rows, fi, fo in pops:
        if fi not in rows.columns:
            skipped.append(key)
            continue
        used = rows[rows[fi] >= 1]
        out.append((key, title, pd.DataFrame({"fi": used[fi].to_numpy(), "fo": used[fo].to_numpy(),
                                              **{v: used[v].to_numpy() for v, _ in PROFILE}})))
    return out, skipped


# ── xmin: where the long tail begins (Clauset, Shalizi and Newman, 2009) ──
def fit_xmin(values):
    """Discrete power law fitted above each candidate xmin; the best candidate has
    the smallest Kolmogorov-Smirnov distance between the data and the fit.
    Returns (xmin, alpha, ks, packages in the tail)."""
    x = np.sort(values[values >= 1]).astype(float)
    if len(x) < XMIN_TAIL:
        return None
    logs = np.log(x)
    suffix = np.concatenate([np.cumsum(logs[::-1])[::-1], [0.0]])
    uniq, counts = np.unique(x, return_counts=True)
    best = None
    for c in uniq[uniq <= XMIN_MAX]:
        start = int(np.searchsorted(x, c))
        n = len(x) - start
        if n < XMIN_TAIL:
            break
        s = suffix[start]
        fit = minimize_scalar(lambda a: n * np.log(zeta(a, c)) + a * s,
                              bounds=(1.01, 6.0), method="bounded")
        alpha = fit.x
        keep = uniq >= c
        emp = np.cumsum(counts[keep]) / n
        model = 1 - zeta(alpha, uniq[keep] + 1) / zeta(alpha, c)
        ks = float(np.max(np.abs(emp - model)))
        if best is None or ks < best[2]:
            best = (int(c), float(alpha), ks, n)
    return best


# ── Curves ───────────────────────────────────────────────────────────
def cuts_for(values, measure):
    """Scale cuts plus decile cuts; each cut keeps the packages with the measure >= cut."""
    labels = {k: [] for k in SCALE[measure]}
    for q in DECILES:
        k = int(np.quantile(values, q, method="lower"))
        labels.setdefault(k, []).append(int(round((1 - q) * 100)))
    return sorted(labels), labels


def decile_label(tops):
    """The requested cuts (top X%) that fall on this cut; several mean ties."""
    if not tops:
        return ""
    return f"{tops[0]}% de arriba" if len(tops) == 1 else f"{tops[0]}% a {tops[-1]}% de arriba"


def curve(pop, measure, xmin=None):
    col = "fi" if measure == "fan_in" else "fo"
    other, _ = OTHER[measure]
    values = pop[col].to_numpy()
    cuts, labels = cuts_for(values, measure)
    if xmin is not None and xmin not in cuts:
        cuts = sorted(cuts + [xmin])
    rows = []
    for k in cuts:
        g = pop[values >= k]
        if len(g) < MIN_N:
            continue
        row = {"cut": k, "deciles": decile_label(labels.get(k, [])), "xmin": k == xmin, "n": len(g),
               "pct": len(g) / len(pop) * 100}
        for v in [v for v, _ in PROFILE] + [other]:
            row[v] = spearman(g[col], g[v])
        rows.append(row)
    t = pd.DataFrame(rows)
    t["n_band"] = t["n"] - t["n"].shift(-1).fillna(0).astype(int)
    return t


def margin(n):
    return max(CHANGE, 3 / np.sqrt(n))


def pattern(t, v):
    """Rises, falls or stays flat as the lower packages are dropped (orientation only)."""
    s = t[v].reset_index(drop=True)
    i_peak = int(s.values.argmax())
    if i_peak > 0 and s.iloc[i_peak] - s.iloc[0] >= margin(t["n"].iloc[i_peak]):
        return f"Sube al cortar: máximo en ≥ {t['cut'].iloc[i_peak]}"
    if s.iloc[0] - s.iloc[-1] >= margin(t["n"].iloc[-1]):
        return "Baja al cortar"
    return "Plana"


def draw(t, measure, title, path):
    other, other_name = OTHER[measure]
    fig, ax = plt.subplots(figsize=(13, 6.4), dpi=200)
    x = np.arange(len(t))
    for (v, name), color in zip(PROFILE + [(other, other_name)], COLORS):
        ax.plot(x, t[v], marker="o", ms=4, lw=2, color=color, label=name)
    ax.axhline(0, color=TEXT, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"≥ {k}\n{p_es(p)}" + ("\nxmin" if m else "")
                        for k, p, m in zip(t["cut"], t["pct"], t["xmin"])], fontsize=9.5)
    for i in np.flatnonzero(t["xmin"].to_numpy()):
        ax.axvline(i, color=SOFT, lw=1, ls="--")
    ax.set_xlabel(f"{MEASURE_NAME[measure]} mínimo del grupo, y qué parte de la población queda",
                  fontsize=11, color=SOFT)
    ax.set_ylabel(f"Correlación de Spearman con el {MEASURE_NAME[measure]}", fontsize=11, color=SOFT)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    ax.set_title(title, loc="left", fontsize=15, color=TEXT, pad=12)
    ax.legend(frameon=False, fontsize=10, loc="center left", bbox_to_anchor=(1.0, 0.5))
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


# ── Reports ──────────────────────────────────────────────────────────
def report(measure, results, skipped, xmins):
    other, other_name = OTHER[measure]
    var_list = PROFILE + [(other, other_name)]
    m = MEASURE_NAME[measure]
    L = [f"# Curvas de cortes por {m}\n",
         f"Generado {time.strftime('%Y-%m-%d %H:%M')}. Cada grupo conserva los paquetes con el {m} igual o "
         f"mayor que el corte. Los cortes vienen de los deciles de cada población, es decir, quedarse con el "
         f"90%, 80%… de arriba (columna Corte pedido por deciles), y de la "
         f"escala {', '.join(str(k) for k in SCALE[measure])}. Se omiten los cortes con menos de "
         f"{n_es(MIN_N)} paquetes.\n",
         "Si varios cortes pedidos caen en la misma fila, es por los empates: no se puede quedar justo con "
         "ese porcentaje, y la columna De la población dice cuánto queda en realidad.\n",
         "Cómo leer cada variable: si su correlación sube al sacar a los de abajo, esos paquetes eran ruido; "
         "si baja desde el principio, no lo eran; si queda plana, el corte no cambia la conclusión.\n"]
    if skipped:
        L.append("Omitidas, porque falta su columna (corre la versión de check_fanin_clean.py que separa el "
                 "Fan-In externo): " + ", ".join(skipped) + ".\n")
    L += [f"## Inicio de la cola (xmin)\n",
          f"Valor del {m} desde el que la distribución entra en su cola larga, estimado con el método de "
          "Clauset, Shalizi y Newman (2009): se ajusta una ley de potencia discreta sobre cada candidato y se "
          "elige el de menor distancia de Kolmogorov-Smirnov. Se agrega como un corte más, marcado con xmin. "
          "No se corre la prueba de bondad de ajuste por bootstrap: es un punto de referencia, no una prueba de "
          "que la cola sea una ley de potencia. Si la cola deja menos de " + n_es(MIN_N) + " paquetes, ese "
          "corte no aparece en las tablas de la curva, porque la correlación sería poco confiable.\n",
          md_table(["Población", "xmin", "Exponente", "Distancia KS", "Paquetes en la cola", "De la población"],
                   [[title, n_es(x[0]), d_es(x[1], 2), d_es(x[2], 3), n_es(x[3]), p_es(x[4])] if x else
                    [title, "—", "—", "—", "—", "—"] for key, title, _ in results for x in [xmins.get(key)]])]
    for key, title, t in results:
        rows = [[f"≥ {r.cut}" + (" (xmin)" if r.xmin else ""), r.deciles or "", n_es(r.n), p_es(r.pct),
                 n_es(r.n_band)]
                + [d_es(getattr(r, v)) for v, _ in var_list] for r in t.itertuples()]
        summary = [[n, d_es(t[v].iloc[0]), d_es(t[v].max()), d_es(t[v].iloc[-1]), pattern(t, v)]
                   for v, n in var_list]
        L += [f"## {title}\n",
              md_table(["Corte", "Corte pedido por deciles", "Paquetes", "De la población",
                        "Hasta el siguiente corte"]
                       + [n for _, n in var_list], rows),
              "Resumen (orientativo: un cambio cuenta si supera " + d_es(CHANGE, 2)
              + " y el margen de azar del grupo, que crece cuando quedan menos paquetes):\n",
              md_table(["Variable", "Con todos", "Máximo", "En el último corte", "Qué hace al cortar"], summary)]
    common = sorted(set.intersection(*[set(t["cut"]) for _, _, t in results]) & set(SCALE[measure]))
    L.append(f"## Comparación entre poblaciones, por variable\n\nCortes de la escala presentes en todas "
             "las poblaciones. Cada celda es la correlación con el " + m + " en ese corte.\n")
    for v, name in var_list:
        rows = []
        for k in common:
            cells = [f"≥ {k}"]
            for _, _, t in results:
                cells.append(d_es(t.loc[t["cut"] == k, v].iloc[0]))
            rows.append(cells)
        L += [f"**{name}:**\n", md_table(["Corte"] + [key for key, _, _ in results], rows)]
    L.append("Claves: " + "; ".join(f"{key} = {title}" for key, title, _ in results) + ".\n")
    (OUT / f"curvas_{measure}.md").write_text("\n".join(L), encoding="utf-8")
    print(f"  curvas_{measure}.md")


def main():
    t0 = time.time()
    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    print(f"Writing to {OUT}")
    df = load()
    pops, skipped = populations(df)
    long_rows = []
    for measure in ("fan_in", "fan_out"):
        other, _ = OTHER[measure]
        results, xmins = [], {}
        for key, title, pop in pops:
            col = "fi" if measure == "fan_in" else "fo"
            fit = fit_xmin(pop[col].to_numpy())
            if fit:
                xmins[key] = fit + ((pop[col] >= fit[0]).mean() * 100,)
            t = curve(pop, measure, fit[0] if fit else None)
            results.append((key, title, t))
            draw(t, measure, f"{title}: correlación con el {MEASURE_NAME[measure]} por corte",
                 OUT / "figures" / f"{measure}_{key}.png")
            for r in t.itertuples():
                for v in [v for v, _ in PROFILE] + [other]:
                    long_rows.append({"measure": measure, "population": key, "cut": r.cut, "is_xmin": r.xmin,
                                      "deciles": r.deciles, "n": r.n, "pct_kept": round(r.pct, 2),
                                      "n_until_next_cut": r.n_band, "variable": v, "rho": getattr(r, v)})
            print(f"  {measure} {key:<9} {len(t)} cuts | {(time.time() - t0) / 60:.1f} min")
        report(measure, results, skipped, xmins)
    pd.DataFrame(long_rows).to_csv(OUT / "curvas.csv", index=False)
    meta = {"executed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "input": {"study": str(STUDY), "clean": str(CLEAN)},
            "params": {"scale": SCALE, "deciles": DECILES, "min_n": MIN_N, "change": CHANGE,
                       "xmin_max": XMIN_MAX, "xmin_tail": XMIN_TAIL,
                       "snapshot_date": str(SNAPSHOT_DATE)},
            "populations": {key: title for key, title, _ in pops}, "skipped": skipped}
    (OUT / "run_metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  curvas.csv and run_metadata.json\nDone in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()