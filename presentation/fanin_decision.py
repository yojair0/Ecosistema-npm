#!/usr/bin/env python3
"""
fanin_decision.py -- Slides to decide the study population: the results of the
07 (Fan-In > 0 population), the 08 (families) and the clean Fan-In recount.

Each image answers one question of the decision:
  1_poblaciones.png          how many packages each population keeps
  2_familias_fan_in.png      how much of the Fan-In comes from the own family
  3_retencion.png            what the population without families keeps, by band and year
  4_correlaciones.png        whether the correlations change between groups G1, G2 and G3
  5_definicion_familia.png   whether counting families before or after cleaning matters
  6_fan_in_limpio.png        how many packages owe their Fan-In to excluded packages
  7_grupos_identicos.png     packages with 100 or more dependents and none inside the
                             population, grouped by identical Fan-In (spam networks)
The same results also come in two combined images, one slide each:
  A_familias.png             images 2, 3 and 4: how much families weigh and what changes
  B_poblacion_y_fan_in.png   images 1, 5, 6 and 7: the population and the clean Fan-In
It also writes diapositivas.md with every number the slides show, resumen.md
with the key numbers, and each table as CSV.

The numbers are computed from the data with the same rules as the 08, so they
match its report. Run it from the repository root, after 07 and
check_fanin_clean.py, wherever this script is stored:
    python presentation/fanin_decision.py

Input : data/fanin_population/fanin_population.parquet
        data/07_inclusion_packages/population_with_families.parquet
        data/07_inclusion_packages/run_metadata.json
        data/exploration/fanin_clean/fanin_clean.parquet   (optional: images 6 and 7)
Output: data/presentation/fanin_decision/
"""
import json
import sys
import time
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
from scipy.stats import rankdata


def repo_root():
    for p in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (p / "data" / "07_inclusion_packages").is_dir():
            return p
    sys.exit("data/07_inclusion_packages not found: run from the repository root")


BASE = repo_root()
STUDY = BASE / "data" / "fanin_population" / "fanin_population.parquet"
POP_A = BASE / "data" / "07_inclusion_packages" / "population_with_families.parquet"
META = BASE / "data" / "07_inclusion_packages" / "run_metadata.json"
CLEAN = BASE / "data" / "exploration" / "fanin_clean" / "fanin_clean.parquet"
OUT = BASE / "data" / "presentation" / "fanin_decision"
SNAPSHOT_DATE = date(2026, 9, 18)
GROUP_MIN, GROUP_FI_MIN = 5, 100
BANDS = [(1, 9, "1-9"), (10, 99, "10-99"), (100, 999, "100-999"), (1000, None, "1000+")]
VARS = [("fan_in_dev", "Dependientes de desarrollo"), ("n_versions", "Versiones"),
        ("n_maintainers", "Mantenedores"), ("age_years", "Edad"), ("has_github", "En GitHub"),
        ("n_keywords", "Palabras clave"), ("scoped", "Tiene scope")]
GROUPS = {"G1": "Con familias", "G2": "Solo vínculos externos", "G3": "Sin familias"}
COLORS = {"G1": "#c4c4bd", "G2": "#93c5fd", "G3": "#2563eb"}
TEXT, SOFT, RULE, HIGHLIGHT, ACCENT = "#111827", "#6b7280", "#e5e7eb", "#dbeafe", "#2563eb"
lines_md = []


# ── Formats (Spanish) ────────────────────────────────────────────────
def n_es(v):
    return f"{int(round(v)):,}".replace(",", ".")


def d_es(v, d=1):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def p_es(v, d=1):
    return d_es(v, d) + "%"


def r_es(v):
    return f"{v:+.3f}".replace(".", ",")


# ── Data ─────────────────────────────────────────────────────────────
def band(values):
    out = pd.Series("", index=values.index)
    for lo, hi, label in BANDS:
        out[(values >= lo) if hi is None else values.between(lo, hi)] = label
    return out


def spearman(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    rx, ry = rankdata(x[m]), rankdata(y[m])
    dx, dy = rx - rx.mean(), ry - ry.mean()
    den = np.sqrt((dx * dx).sum() * (dy * dy).sum())
    return float((dx * dy).sum() / den) if den > 0 else np.nan


def load():
    cols = ["name", "scope", "scope_size", "created_date", "created_year", "fan_in",
            "fan_in_internal", "fan_in_external", "fan_out", "fan_out_external",
            "fan_in_dev", "n_versions", "n_maintainers", "n_keywords", "has_github"]
    df = pd.read_parquet(STUDY, columns=cols)
    df["age_years"] = (pd.Timestamp(SNAPSHOT_DATE) - pd.to_datetime(df["created_date"])).dt.days / 365.25
    df["scoped"] = (df["scope"].fillna("") != "").astype(np.int8)
    df["has_github"] = df["has_github"].fillna(0).astype(bool).astype(np.int8)
    scopes = pd.read_parquet(POP_A, columns=["scope"])["scope"].fillna("")
    clean_sizes = scopes[scopes != ""].value_counts()
    df["scope_size_clean"] = df["scope"].map(clean_sizes).fillna(0).astype("int32")
    df["band"] = band(df["fan_in"])
    if CLEAN.exists():
        clean = pd.read_parquet(CLEAN, columns=["name", "fan_in_clean"])
        df = df.merge(clean, on="name", how="left")
    meta = json.loads(META.read_text(encoding="utf-8"))["counts"]
    return df, meta


def groups(df):
    return {"G1": (df, "fan_in", "fan_out"),
            "G2": (df[df["fan_in_external"] > 0], "fan_in_external", "fan_out_external"),
            "G3": (df[df["scope_size"] < 2], "fan_in", "fan_out"),
            "G4": (df[df["scope_size_clean"] < 2], "fan_in", "fan_out")}


# ── Drawing helpers ─────────────────────────────────────────────────
W_IN, H_IN = 16, 9


def new_slide(title):
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=200)
    fig.text(0.6 / W_IN, 1 - 0.6 / H_IN, title, fontsize=22, color=TEXT, va="center")
    return fig


def axes_in(fig, left, top, width, height):
    """Axes placed in inches from the top left corner of the slide."""
    return fig.add_axes([left / W_IN, 1 - (top + height) / H_IN, width / W_IN, height / H_IN])


def text_in(fig, left, top, text, size=13, color=TEXT, **kw):
    fig.text(left / W_IN, 1 - top / H_IN, text, fontsize=size, color=color, va="center", **kw)


def table_in(fig, left, top, widths, row_h, header, rows, align, highlight=(), font=13):
    ax = axes_in(fig, left, top, sum(widths), row_h * (len(rows) + 1))
    total = sum(widths)
    ax.set_xlim(0, total)
    ax.set_ylim(len(rows) + 1, 0)
    ax.axis("off")

    def put(text, x, w, y, a, bold=False):
        xx, ha = (x + 0.12, "left") if a == "left" else (x + w - 0.12, "right")
        ax.text(xx, y, text, ha=ha, va="center", fontsize=font, color=TEXT,
                fontweight="bold" if bold else "normal")

    x = 0
    for h, w, a in zip(header, widths, align):
        put(h, x, w, 0.5, a, bold=True)
        x += w
    ax.plot([0, total], [1, 1], color=TEXT, lw=1.3)
    for i, r in enumerate(rows):
        x = 0
        for j, (cell, w, a) in enumerate(zip(r, widths, align)):
            if (i, j) in highlight:
                ax.add_patch(Rectangle((x, i + 1), w, 1, color=HIGHLIGHT, zorder=0))
            put(cell, x, w, i + 1.5, a)
            x += w
        ax.plot([0, total], [i + 2] * 2, color=RULE, lw=0.8)


def clean_axes(ax):
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.set_yticks([])


def label_bars(ax, bars, fmt, size=11, offset=0.8):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + (offset if h >= 0 else -offset), fmt(h),
                ha="center", va="bottom" if h >= 0 else "top", fontsize=size, color=TEXT)


def save_slide(fig, name):
    fig.savefig(OUT / f"{name}.png", facecolor="white")
    plt.close(fig)
    print(f"  {name}.png")


def save_csv(name, header, rows):
    pd.DataFrame(rows, columns=header).to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8-sig")


# ── Numbers ──────────────────────────────────────────────────────────
def populations(df, meta):
    g1, g3 = len(df), int((df["scope_size"] < 2).sum())
    rows = [("Universo: la red completa", n_es(meta["n_universe"]), "—"),
            ("A: pasa la limpieza, con familias", n_es(meta["n_A"]),
             p_es(meta["n_A"] / meta["n_universe"] * 100)),
            ("B: A sin familias", n_es(meta["n_B"]), p_es(meta["n_B"] / meta["n_A"] * 100)),
            ("Estudio con familias: A con Fan-In > 0", n_es(g1), p_es(g1 / meta["n_A"] * 100)),
            ("Estudio sin familias: B con Fan-In > 0", n_es(g3), p_es(g3 / meta["n_B"] * 100))]
    lines_md.append(f"- De la población A, solo el {p_es(g1 / meta['n_A'] * 100)} tiene algún dependiente "
                    f"({n_es(g1)} paquetes); de la B, el {p_es(g3 / meta['n_B'] * 100)} ({n_es(g3)}).")
    return rows, g1 / meta["n_A"] * 100


def families(df):
    internal, only_int = [], []
    for _, _, lab in BANDS:
        m = df["band"] == lab
        internal.append(df.loc[m, "fan_in_internal"].sum() / df.loc[m, "fan_in"].sum() * 100)
        only_int.append((df.loc[m, "fan_in_external"] == 0).mean() * 100)
    total_int = df["fan_in_internal"].sum() / df["fan_in"].sum() * 100
    total_only = (df["fan_in_external"] == 0).mean() * 100
    lines_md.append(f"- Con familias, el {p_es(total_int)} del Fan-In es interno y el {p_es(total_only)} de "
                    f"los paquetes usados solo lo usa su familia; en el tramo 1-9, el {p_es(only_int[0])}.")
    return internal, only_int, total_int, total_only


def retention(df):
    stays = df["scope_size"] < 2
    by_band = [stays[df["band"] == lab].mean() * 100 for _, _, lab in BANDS]
    years = df.groupby("created_year")["scope_size"].apply(lambda s: (s < 2).mean() * 100)
    years = years[years.index >= 2012]
    lines_md.append(f"- Sin familias se conserva el {p_es(by_band[0])} del tramo 1-9 y el {p_es(by_band[-1])} del "
                    f"tramo 1000+. Por año, 2024 conserva el {p_es(years.get(2024, np.nan))}, contra "
                    f"{p_es(years.get(2023, np.nan))} en 2023 y {p_es(years.get(2025, np.nan))} en 2025.")
    return by_band, years


def correlations(df):
    res = {}
    for g, (sub, fi, fo) in groups(df).items():
        res[g] = {"fi": {v: spearman(sub[fi], sub[v]) for v, _ in VARS},
                  "fo": {v: spearman(sub[fo], sub[v]) for v, _ in VARS}, "n": len(sub)}
    diff = max(abs(res["G3"]["fi"][v] - res["G2"]["fi"][v]) for v, _ in VARS)
    s1, s2 = res["G1"]["fo"]["scoped"], res["G2"]["fo"]["scoped"]
    lines_md.append(f"- G3 y G2 difieren a lo más en {d_es(diff, 3)} con el Fan-In. Con el Fan-Out, tener scope "
                    f"pasa de {r_es(s1)} con familias a {r_es(s2)} contando solo vínculos externos.")
    return res, diff


def definition(res):
    n3, n4 = res["G3"]["n"], res["G4"]["n"]
    dfi = max(abs(res["G4"]["fi"][v] - res["G3"]["fi"][v]) for v, _ in VARS)
    dfo = max(abs(res["G4"]["fo"][v] - res["G3"]["fo"][v]) for v, _ in VARS)
    rows = [("Paquetes", n_es(n3), n_es(n4)),
            ("Diferencia de paquetes", "—", ("+" if n4 >= n3 else "−") + n_es(abs(n4 - n3))),
            ("Mayor diferencia de ρ con el Fan-In", "—", d_es(dfi, 3)),
            ("Mayor diferencia de ρ con el Fan-Out", "—", d_es(dfo, 3))]
    lines_md.append(f"- G3 y G4 difieren en {n_es(abs(n4 - n3))} paquetes y a lo más en {d_es(max(dfi, dfo), 3)} "
                    "en ρ: la definición de familia no cambia la decisión.")
    return rows


def clean_table(df):
    rows, total = [], {"A": [0, 0, 0], "B": [0, 0, 0]}
    clean_band = band(df["fan_in_clean"]).where(df["fan_in_clean"] > 0, "0")
    nofam = df["scope_size"] < 2
    for _, _, lab in BANDS:
        cells = [f"Fan-In {lab}"]
        for key, mask in [("A", pd.Series(True, index=df.index)), ("B", nofam)]:
            m = (df["band"] == lab) & mask
            drop = int((m & (df["fan_in_clean"] == 0)).sum())
            moved = int((m & (clean_band != df["band"])).sum())
            total[key][0] += int(m.sum()); total[key][1] += drop; total[key][2] += moved
            cells += [n_es(drop), p_es(moved / m.sum() * 100 if m.sum() else 0)]
        rows.append(cells)
    rows.append(["Total"] + [x for key in ("A", "B") for x in
                             (n_es(total[key][1]), p_es(total[key][2] / total[key][0] * 100))])
    b = total["B"]
    lines_md.append(f"- Sin familias, {n_es(b[1])} paquetes ({p_es(b[1] / b[0] * 100)}) deben todo su Fan-In a "
                    f"paquetes excluidos, y el {p_es(b[2] / b[0] * 100)} cambia de tramo con el Fan-In limpio.")
    return rows


def hubs_table(df):
    """Hubs: Fan-In of GROUP_FI_MIN or more and no dependent inside population A.
    Among them chance collisions are rare, so an identical Fan-In shared by
    GROUP_MIN or more packages is the pattern of a spam network."""
    hubs = df[(df["fan_in"] >= GROUP_FI_MIN) & (df["fan_in_clean"] == 0)]
    counts = hubs["fan_in"].value_counts()
    in_groups = int(hubs["fan_in"].map(counts).ge(GROUP_MIN).sum())
    shared = counts[counts >= GROUP_MIN].sort_index(ascending=False)
    rows = []
    for value, k in shared.head(9).items():
        names = hubs.loc[hubs["fan_in"] == value, "name"].head(3)
        rows.append((n_es(value), n_es(k), ", ".join(names) + (", …" if k > 3 else "")))
    n_nofam = int((hubs["scope_size"] < 2).sum())
    lines_md.append(f"- {n_es(len(hubs))} paquetes con Fan-In de {GROUP_FI_MIN} o más no tienen ningún dependiente "
                    f"en la población ({n_es(n_nofam)} sin familias); {n_es(in_groups)} de ellos comparten "
                    f"exactamente su Fan-In con {GROUP_MIN - 1} o más: el patrón de las redes de spam.")
    return rows, len(hubs), n_nofam, in_groups


# ── Slides ───────────────────────────────────────────────────────────
def slide1(pop_rows, pct_used, fam, ret):
    fig = new_slide("La población de estudio y el peso de las familias")
    # 1 populations
    text_in(fig, 0.6, 1.3, "1. Cuántos paquetes quedan", 15)
    table_in(fig, 0.6, 1.6, [4.3, 1.45, 1.55], 0.46, ["Población", "Paquetes", "Del anterior"],
             pop_rows, ["left", "right", "right"], {(3, 1), (4, 1)}, font=12)
    text_in(fig, 0.6, 4.6, f"Cada porcentaje es sobre la fila anterior: el {p_es(pct_used)} de la "
            "población A tiene algún dependiente.", 11, SOFT)
    # 2 families
    internal, only_int, total_int, total_only = fam
    text_in(fig, 8.6, 1.3, "2. Cuánto pesa la propia familia, por tramo de Fan-In", 15)
    ax = axes_in(fig, 8.6, 1.75, 7.0, 2.45)
    x, w = np.arange(len(BANDS)), 0.38
    label_bars(ax, ax.bar(x - w / 2, internal, w, color="#93c5fd", label="Fan-In que viene de la familia"),
               p_es, 10)
    label_bars(ax, ax.bar(x + w / 2, only_int, w, color=ACCENT, label="Paquetes que solo usa su familia"),
               p_es, 10)
    ax.set_xticks(x)
    ax.set_xticklabels([lab for _, _, lab in BANDS], fontsize=11)
    ax.set_ylim(0, max(internal + only_int) * 1.3)
    ax.legend(frameon=False, fontsize=10, loc="upper right")
    clean_axes(ax)
    text_in(fig, 8.6, 4.6, f"En total: el {p_es(total_int)} del Fan-In es interno, y el {p_es(total_only)} "
            "de los paquetes usados solo lo usa su familia.", 11, SOFT)
    # 3 retention
    by_band, years = ret
    text_in(fig, 0.6, 5.25, "3. Qué parte de los paquetes usados conserva la población sin familias", 15)
    a1 = axes_in(fig, 0.6, 5.7, 5.4, 2.55)
    label_bars(a1, a1.bar([lab for _, _, lab in BANDS], by_band, color=ACCENT, width=0.6), p_es, 10)
    a1.set_ylim(0, 112)
    a1.set_title("Por tramo de Fan-In", loc="left", fontsize=12, color=TEXT)
    a1.tick_params(axis="x", labelsize=11)
    clean_axes(a1)
    a2 = axes_in(fig, 6.8, 5.7, 8.8, 2.55)
    a2.plot(years.index.astype(int), years.values, color=ACCENT, lw=2.2, marker="o", ms=4)
    for yr in (2023, 2024, 2025):
        if yr in years.index:
            a2.annotate(p_es(years[yr]), (yr, years[yr]), textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=10, color=TEXT)
    a2.set_ylim(0, 112)
    a2.set_title("Por año de creación", loc="left", fontsize=12, color=TEXT)
    a2.tick_params(axis="x", labelsize=10)
    clean_axes(a2)
    text_in(fig, 0.6, 8.65, "Ejemplo: de cada 100 paquetes usados del tramo 1-9, quedan "
            f"{d_es(by_band[0], 0)} sin familia.", 11, SOFT)
    save_slide(fig, "diapositiva_1_poblacion_y_familias")


def slide2(res, diff, def_rows):
    fig = new_slide("Las correlaciones y la definición de familia")
    text_in(fig, 0.6, 1.3, "4. Correlación de Spearman con el Fan-In, entre los paquetes usados", 15)
    ax = axes_in(fig, 0.6, 1.8, 14.8, 3.3)
    x, w = np.arange(len(VARS)), 0.27
    for k, g in enumerate(["G1", "G2", "G3"]):
        vals = [res[g]["fi"][v] for v, _ in VARS]
        bars = ax.bar(x + (k - 1) * w, vals, w, color=COLORS[g], label=f"{g}: {GROUPS[g]}")
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + (0.006 if v >= 0 else -0.006), d_es(v, 2),
                    ha="center", va="bottom" if v >= 0 else "top", fontsize=9, color=TEXT)
    ax.axhline(0, color=TEXT, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([n for _, n in VARS], fontsize=11)
    lo = min(min(res[g]["fi"].values()) for g in ["G1", "G2", "G3"])
    hi = max(max(res[g]["fi"].values()) for g in ["G1", "G2", "G3"])
    ax.set_ylim(min(lo, 0) - 0.05, hi + 0.07)
    ax.legend(frameon=False, fontsize=10, loc="upper right", ncol=3)
    clean_axes(ax)
    text_in(fig, 0.6, 5.5, "ρ va de −1 a 1: 0 es sin relación, y 0,2 es una relación débil. "
            f"Sin familias (G3) y solo vínculos externos (G2) difieren a lo más en {d_es(diff, 3)}.",
            11, SOFT)
    text_in(fig, 0.6, 6.2, "5. Contar las familias antes o después de limpiar", 15)
    table_in(fig, 0.6, 6.5, [6.2, 3.4, 3.8], 0.4,
             ["Sin familias, contadas…", "En el registro (G3)", "Después de limpiar (G4)"],
             def_rows, ["left", "right", "right"], font=12)
    save_slide(fig, "diapositiva_2_correlaciones")


def slide3(rows):
    fig = new_slide("Fan-In contado solo con dependientes que están en la población")
    table_in(fig, 0.6, 1.5, [2.8, 3.3, 2.7, 3.3, 2.7], 0.62,
             ["Tramo", "Con familias: bajan a 0", "Cambian de tramo", "Sin familias: bajan a 0",
              "Cambian de tramo"], rows, ["left", "right", "right", "right", "right"],
             {(2, 3), (2, 4), (3, 3), (3, 4)}, font=14)
    text_in(fig, 0.6, 6.0, "Bajan a 0: todos sus dependientes quedaron fuera de la población.", 13, SOFT)
    text_in(fig, 0.6, 6.5, "Cambian de tramo: el Fan-In limpio cae en otro tramo; por ejemplo, de 12 "
            "dependientes a 8 pasa de 10-99 a 1-9.", 13, SOFT)
    save_slide(fig, "diapositiva_3_fan_in_limpio")


def slide4(rows, n_hubs, n_nofam, in_groups):
    fig = new_slide("Paquetes con 100 o más dependientes, ninguno dentro de la población")
    text_in(fig, 0.6, 1.35, f"{n_es(n_hubs)} paquetes en total, {n_es(n_nofam)} de ellos sin familias. "
            f"{n_es(in_groups)} comparten exactamente su Fan-In con {GROUP_MIN - 1} o más.", 15)
    if rows:
        table_in(fig, 0.6, 1.8, [2.0, 2.0, 10.8], 0.58, ["Fan-In", "Paquetes", "Ejemplos"], rows,
                 ["right", "right", "left"], font=14)
    text_in(fig, 0.6, 8.4, "Que varios paquetes tengan exactamente el mismo Fan-In, sin ningún dependiente "
            "dentro de la población, es la huella de una red de spam: probablemente, los mismos paquetes "
            "falsos dependen de todos ellos.", 12, SOFT)
    save_slide(fig, "diapositiva_4_centros_de_spam")


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]) + "\n"


def write_slides_md(pop_rows, fam, ret, res, diff, def_rows, rows6=None, hubs=None):
    internal, only_int, total_int, total_only = fam
    by_band, years = ret
    bands = [lab for _, _, lab in BANDS]
    L = ["# Diapositivas para decidir la población de estudio\n",
         f"Generado {time.strftime('%Y-%m-%d %H:%M')}. Cada sección repite las cifras de una diapositiva.\n",
         "## Diapositiva 1 · La población de estudio y el peso de las familias\n",
         "### 1. Cuántos paquetes quedan\n",
         md_table(["Población", "Paquetes", "Del anterior"], pop_rows),
         "### 2. Cuánto pesa la propia familia, por tramo de Fan-In\n",
         md_table(["Tramo", "Fan-In que viene de la familia", "Paquetes que solo usa su familia"],
                  [[b, p_es(i), p_es(o)] for b, i, o in zip(bands, internal, only_int)]
                  + [["Total", p_es(total_int), p_es(total_only)]]),
         "### 3. Qué parte de los paquetes usados conserva la población sin familias\n",
         "Por tramo de Fan-In:\n",
         md_table(["Tramo", "Se conserva"], [[b, p_es(v)] for b, v in zip(bands, by_band)]),
         "Por año de creación:\n",
         md_table(["Año", "Se conserva"], [[str(int(y)), p_es(v)] for y, v in years.items()]),
         "## Diapositiva 2 · Las correlaciones y la definición de familia\n",
         "### 4. Correlación de Spearman, entre los paquetes usados\n",
         f"G1: {GROUPS['G1']}. G2: {GROUPS['G2']}. G3: {GROUPS['G3']}. "
         f"G2 y G3 difieren a lo más en {d_es(diff, 3)} con el Fan-In.\n",
         "Con el Fan-In:\n",
         md_table(["Variable", "G1", "G2", "G3"],
                  [[n] + [r_es(res[g]["fi"][v]) for g in ("G1", "G2", "G3")] for v, n in VARS]),
         "Con el Fan-Out (no está en la diapositiva; sirve para responder preguntas):\n",
         md_table(["Variable", "G1", "G2", "G3"],
                  [[n] + [r_es(res[g]["fo"][v]) for g in ("G1", "G2", "G3")] for v, n in VARS]),
         "### 5. Contar las familias antes o después de limpiar\n",
         md_table(["Sin familias, contadas…", "En el registro (G3)", "Después de limpiar (G4)"], def_rows)]
    if rows6 is not None:
        L += ["## Diapositiva 3 · Fan-In contado solo con dependientes que están en la población\n",
              md_table(["Tramo", "Con familias: bajan a 0", "Cambian de tramo", "Sin familias: bajan a 0",
                        "Cambian de tramo"], rows6)]
    if hubs is not None:
        rows7, n_hubs, n_nofam, in_groups = hubs
        L += ["## Diapositiva 4 · Paquetes con 100 o más dependientes, ninguno dentro de la población\n",
              f"{n_es(n_hubs)} paquetes en total, {n_es(n_nofam)} de ellos sin familias. {n_es(in_groups)} "
              f"comparten exactamente su Fan-In con {GROUP_MIN - 1} o más.\n",
              md_table(["Fan-In", "Paquetes", "Ejemplos"], rows7)]
    (OUT / "diapositivas.md").write_text("\n".join(L), encoding="utf-8")
    print("  diapositivas.md")


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Writing to {OUT}")
    df, meta = load()
    pop_rows, pct_used = populations(df, meta)
    fam = families(df)
    ret = retention(df)
    res, diff = correlations(df)
    def_rows = definition(res)
    save_csv("1_poblaciones", ["Población", "Paquetes", "Del anterior"], pop_rows)
    save_csv("5_definicion_familia", ["Medida", "G3", "G4"], def_rows)
    slide1(pop_rows, pct_used, fam, ret)
    slide2(res, diff, def_rows)
    rows6 = hubs = None
    if "fan_in_clean" in df.columns:
        rows6 = clean_table(df)
        save_csv("6_fan_in_limpio", ["Tramo", "A: bajan a 0", "A: cambian", "B: bajan a 0", "B: cambian"],
                 rows6)
        slide3(rows6)
        hubs = hubs_table(df)
        save_csv("7_centros_de_spam", ["Fan-In", "Paquetes", "Ejemplos"], hubs[0])
        slide4(*hubs)
    else:
        print("  slides 3 and 4 skipped: run check_fanin_clean.py first")
    write_slides_md(pop_rows, fam, ret, res, diff, def_rows, rows6, hubs)
    text = ["# Cifras para decidir la población de estudio\n",
            f"Generado {time.strftime('%Y-%m-%d %H:%M')} desde el 07, el 08 y el recuento del Fan-In limpio.\n",
            *lines_md, "",
            "## Opciones\n",
            "- Población: con familias (G1), solo vínculos externos (G2) o sin familias (G3).",
            "- Familias contadas en el registro (G3) o después de limpiar (G4).",
            "- Fan-In del registro o Fan-In limpio, que deja fuera a los paquetes que solo usan paquetes excluidos."]
    (OUT / "resumen.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(f"Done in {(time.time() - t0) / 60:.1f} min: {OUT / 'resumen.md'}")


if __name__ == "__main__":
    main()