#!/usr/bin/env python3
"""
09_presentation_assets.py -- the tables and graphs of the sprint 3
presentation, as images ready for Canva.

It reads only result files, so every number matches the last run:
  data/07_inclusion_packages/run_metadata.json
  data/07_inclusion_packages/inclusion_flags.parquet            universe
  data/07_inclusion_packages/population_with_families.parquet   population A
  data/07_inclusion_packages/population_without_families.parquet population B
  data/08b_variable_selection/variable_selection_results.md     correlations, R2
  stratification/results/<technique>/metrics.csv

Writes data/09_presentation/ (slide numbers of the presentation):
  tabla1_universo.png          slide 5   the 4 million before cleaning
  tabla2_familias.png          slide 7   with and without families
  grafico1_familias.png        slide 8   how families change the correlations
  grafico2_correlaciones.png   slide 9   correlations without families
  tabla3_tecnicas.png          slide 10  stratification techniques
  and each table as .csv.

Run it from the repository root, after 07b, 08b and the stratification scripts.
"""
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
INC = ROOT / "data" / "07_inclusion_packages"
MD_08B = ROOT / "data" / "08b_variable_selection" / "variable_selection_results.md"
STRAT = ROOT / "stratification" / "results"
OUT = ROOT / "data" / "09_presentation"

HIGHLIGHT = "#dbeafe"
TEXT = "#111827"
SOFT = "#6b7280"
RULE = "#e5e7eb"
COLORS = {"A": "#c4c4bd", "A externo": "#93c5fd", "B": "#2563eb"}
GROUP_LABELS = {"A": "Con familias", "A externo": "Con familias, solo vínculos externos",
                "B": "Sin familias"}

PICKS = [
    ("01_grid_base", "medium_nocensus", "Cuadrícula por décadas", "la posición, en tramos fijos"),
    ("02_optimal_cuts", "bands3_nocensus", "Cortes óptimos", "la posición, en tramos calculados"),
    ("03_regression_tree", "leaves15", "Árbol de regresión", "el perfil, dentro de cada grupo"),
    ("04_clustering", "k12", "Clustering k-means", "el perfil del paquete"),
]
# Variables of the two graphs, with their names on the slides
FAMILY_VARS = [("n_versions", "Versiones"), ("age_years", "Edad"),
               ("n_maintainers", "Mantenedores"), ("has_github", "En GitHub"),
               ("scoped", "Tiene scope")]
B_VARS = [("fan_in_dev", "Dependientes de desarrollo"), ("fan_out_dev", "Dependencias de desarrollo"),
          ("n_versions", "Versiones"), ("age_years", "Edad"), ("n_maintainers", "Mantenedores"),
          ("has_github", "En GitHub"), ("n_keywords", "Palabras clave")]


# ── Spanish number formats ───────────────────────────────────────────
def n_es(v):
    return f"{int(round(v)):,}".replace(",", ".")


def dec_es(v, d=1):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct_es(v, d=1):
    return dec_es(v, d) + "%"


def num_es(v):
    return n_es(v) if float(v).is_integer() else dec_es(v, 1)


# ── Tables ───────────────────────────────────────────────────────────
def draw_table(path, header, rows, widths, align, highlight=(), font=15):
    """One table as a PNG: bold header, thin rules, highlighted cells."""
    row_h = 0.62
    width, height = sum(widths), row_h * (len(rows) + 1) + 0.12
    fig = plt.figure(figsize=(width, height), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.axis("off")
    pad = 0.15

    def put(text, x, w, y, a, bold=False):
        xx, ha = (x + pad, "left") if a == "left" else (x + w - pad, "right")
        ax.text(xx, y, text, ha=ha, va="center", fontsize=font,
                fontweight="bold" if bold else "normal", color=TEXT)

    x = 0
    for h, w, a in zip(header, widths, align):
        put(h, x, w, row_h / 2 + 0.06, a, bold=True)
        x += w
    ax.plot([0, width], [row_h + 0.06] * 2, color=TEXT, lw=1.4)
    for i, row in enumerate(rows):
        y0 = row_h * (i + 1) + 0.06
        x = 0
        for j, (cell, w, a) in enumerate(zip(row, widths, align)):
            if (i, j) in highlight:
                ax.add_patch(Rectangle((x, y0), w, row_h, color=HIGHLIGHT, zorder=0))
            put(cell, x, w, y0 + row_h / 2, a)
            x += w
        ax.plot([0, width], [y0 + row_h] * 2, color=RULE, lw=0.9)
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)


def save_table(name, header, rows, widths, align, highlight):
    draw_table(OUT / f"{name}.png", header, rows, widths, align, highlight)
    pd.DataFrame(rows, columns=header).to_csv(OUT / f"{name}.csv", index=False,
                                              encoding="utf-8-sig")
    print(f"  {name}.png and {name}.csv")


def mill_es(v):
    return dec_es(v / 1e6, 1) + " millones"


def triple(s):
    return f"{n_es(s.median())} / {n_es(s.quantile(0.99))} / {n_es(s.max())}"


def table1_universe():
    f = pd.read_parquet(INC / "inclusion_flags.parquet",
                        columns=["fan_in", "fan_out", "scope_size", "created_year"])
    n = len(f)
    families = int((f["scope_size"] >= 2).sum())
    years = f["created_year"].dropna()
    rows = [
        ("Paquetes", n_es(n)),
        ("Dependencias entre paquetes existentes", mill_es(f["fan_in"].sum())),
        ("Sin ningún dependiente (Fan-In 0)", pct_es((f["fan_in"] == 0).mean() * 100)),
        ("Sin ninguna dependencia declarada (Fan-Out 0)", pct_es((f["fan_out"] == 0).mean() * 100)),
        ("Fan-In: mediana / p99 / máximo", triple(f["fan_in"])),
        ("Fan-Out: mediana / p99 / máximo", triple(f["fan_out"])),
        ("En familias (scope con 2 o más paquetes)", f"{n_es(families)} ({pct_es(families / n * 100)})"),
        ("Creados desde 2024", pct_es((years >= 2024).mean() * 100)),
    ]
    save_table("tabla1_universo", ["Estadístico", "Valor"], rows, [7.4, 3.6],
               ["left", "right"], {(2, 0), (2, 1)})


def profile(path, snap):
    d = pd.read_parquet(path, columns=["fan_in", "fan_out", "n_versions", "created_date",
                                       "has_github", "scope"])
    age = (snap - pd.to_datetime(d["created_date"])).dt.days / 365.25
    fi0, fo0 = d["fan_in"] == 0, d["fan_out"] == 0
    return [
        n_es(len(d)),
        pct_es(fi0.mean() * 100),
        pct_es(fo0.mean() * 100),
        pct_es((fi0 & fo0).mean() * 100),
        num_es(d["n_versions"].median()),
        dec_es(age.median()),
        pct_es(d["has_github"].fillna(False).astype(bool).mean() * 100),
        pct_es((d["scope"].fillna("") != "").mean() * 100),
    ]


def table2_families(meta):
    snap = pd.Timestamp(meta["params"]["SNAPSHOT_DATE"])
    a = profile(INC / "population_with_families.parquet", snap)
    b = profile(INC / "population_without_families.parquet", snap)
    names = ["Paquetes", "Sin ningún dependiente", "Sin ninguna dependencia",
             "Aislados (ni dependientes ni dependencias)", "Versiones (mediana)",
             "Edad en años (mediana)", "En GitHub", "Con scope"]
    rows = [(n, x, y) for n, x, y in zip(names, a, b)]
    save_table("tabla2_familias", ["Después de limpiar", "Con familias", "Sin familias"],
               rows, [6.4, 2.9, 2.9], ["left", "right", "right"], {(1, 1), (1, 2), (7, 1), (7, 2)})


def table3_techniques():
    rows = []
    for tech, config, name, how in PICKS:
        m = pd.read_csv(STRAT / tech / "metrics.csv")
        r = m[m["config"] == config].iloc[0]
        rows.append((name, how, str(int(r["K"])), pct_es(r["r2_log_fi"] * 100, 0),
                     pct_es(r["r2_log_fo"] * 100, 0)))
    save_table("tabla3_tecnicas",
               ["Técnica", "Divide según", "Estratos", "Separa el Fan-In", "Separa el Fan-Out"],
               rows, [3.3, 4.5, 1.6, 2.5, 2.7], ["left", "left", "right", "right", "right"],
               {(0, 3), (0, 4), (1, 3), (1, 4)})
    cuts = pd.read_csv(STRAT / "02_optimal_cuts" / "metrics.csv")
    params = cuts.loc[cuts["config"] == "bands4_nocensus", "params"].iloc[0]
    edges = re.search(r"fi_edges=(\[[^\]]*\])", params)
    if edges:
        print(f"  optimal cuts with four bands, Fan-In edges: {edges.group(1)}")


# ── Values from the 08b report ───────────────────────────────────────
def read_08b():
    """Comparison table of the 08b report: {(name, target): (A, A externo, B)}."""
    vals = {}
    num = r"\s*(-?[\d,]+)\s*"
    for line in MD_08B.read_text(encoding="utf-8").splitlines():
        m = re.match(rf"^\|\s*ρ (\w+) – (Fan-In|Fan-Out)\s*\|{num}\|{num}\|{num}\|", line)
        if m:
            vals[(m.group(1), m.group(2))] = tuple(float(x.replace(",", ".")) for x in m.groups()[2:])
            continue
        m = re.match(rf"^\|\s*(R²|AUC) (Fan-In|Fan-Out)\s*\|{num}\|{num}\|{num}\|", line)
        if m:
            vals[(m.group(1), m.group(2))] = tuple(float(x.replace(",", ".")) for x in m.groups()[2:])
            continue
        m = re.match(rf"^\|\s*ρ Fan-In ↔ Fan-Out\s*\|{num}\|{num}\|{num}\|", line)
        if m:
            vals[("fi_fo", "both")] = tuple(float(x.replace(",", ".")) for x in m.groups())
    return vals


def label_bar(ax, x, y, value, horizontal=False):
    text = dec_es(value, 2)
    if horizontal:
        ax.text(y + (0.006 if y >= 0 else -0.006), x, text, va="center",
                ha="left" if y >= 0 else "right", fontsize=10, color=TEXT)
    else:
        ax.text(x, y + (0.006 if y >= 0 else -0.006), text, ha="center",
                va="bottom" if y >= 0 else "top", fontsize=10, color=TEXT)


def graph1_families(vals):
    groups = ["A", "A externo", "B"]
    names = [n for _, n in FAMILY_VARS]
    data = np.array([vals[(v, "Fan-In")] for v, _ in FAMILY_VARS])
    age, scope = data[1], data[4]
    fig, ax = plt.subplots(figsize=(12, 5.8), dpi=200)
    w = 0.26
    x = np.arange(len(names))
    for k, g in enumerate(groups):
        ax.bar(x + (k - 1) * w, data[:, k], w, color=COLORS[g], label=GROUP_LABELS[g])
        for xi, v in zip(x + (k - 1) * w, data[:, k]):
            label_bar(ax, xi, v, v)
    ax.axhline(0, color=TEXT, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=13)
    ax.set_yticks([])
    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(False)
    ax.set_title(f"Sin familias, la edad pesa {age[2] / age[0]:.1f} veces más y el scope "
                 f"cambia de signo".replace(".", ","), loc="left", fontsize=17, color=TEXT, pad=18)
    ax.text(0, 1.01, "Correlación de Spearman de cada variable con el Fan-In",
            transform=ax.transAxes, fontsize=12, color=SOFT)
    ax.legend(frameon=False, fontsize=11, loc="upper right", ncol=3)
    lo, hi = data.min(), data.max()
    ax.set_ylim(min(lo, 0) - 0.04, hi + 0.06)
    fig.tight_layout()
    fig.savefig(OUT / "grafico1_familias.png", facecolor="white")
    plt.close(fig)
    print("  grafico1_familias.png")


def graph2_correlations(vals):
    names = [n for _, n in B_VARS]
    fi = np.array([vals[(v, "Fan-In")][2] for v, _ in B_VARS])
    fo = np.array([vals[(v, "Fan-Out")][2] for v, _ in B_VARS])
    r2_fi, r2_fo = vals[("R²", "Fan-In")][2], vals[("R²", "Fan-Out")][2]
    fifo = vals[("fi_fo", "both")][2]
    top = max(np.abs(fi).max(), np.abs(fo).max())
    fig, ax = plt.subplots(figsize=(12, 6.2), dpi=200)
    h = 0.38
    y = np.arange(len(names))[::-1]
    ax.barh(y + h / 2, fi, h, color="#2563eb", label="Con el Fan-In")
    ax.barh(y - h / 2, fo, h, color="#f59e0b", label="Con el Fan-Out")
    for yi, v in zip(y + h / 2, fi):
        label_bar(ax, yi, v, v, horizontal=True)
    for yi, v in zip(y - h / 2, fo):
        label_bar(ax, yi, v, v, horizontal=True)
    ax.axvline(0, color=TEXT, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=13)
    ax.set_xticks([])
    for side in ["top", "right", "bottom", "left"]:
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(min(fi.min(), fo.min(), 0) - 0.06, top + 0.08)
    ax.set_title(f"Sin familias, ninguna variable del perfil pasa de {dec_es(top, 2)} con la posición",
                 loc="left", fontsize=17, color=TEXT, pad=52)
    ax.text(0, 1.02, f"Correlación de Spearman. Fan-In y Fan-Out entre sí: {dec_es(fifo, 2)}.\n"
                     f"Con todo el perfil, un modelo explica el {pct_es(r2_fi * 100, 0)} del Fan-In "
                     f"y el {pct_es(r2_fo * 100, 0)} del Fan-Out.",
            transform=ax.transAxes, fontsize=12, color=SOFT, va="bottom")
    ax.legend(frameon=False, fontsize=11, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "grafico2_correlaciones.png", facecolor="white")
    plt.close(fig)
    print("  grafico2_correlaciones.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = json.loads((INC / "run_metadata.json").read_text(encoding="utf-8"))
    print(f"Writing to {OUT}")
    table1_universe()
    table2_families(meta)
    vals = read_08b()
    graph1_families(vals)
    graph2_correlations(vals)
    table3_techniques()
    print("Done.")


if __name__ == "__main__":
    main()