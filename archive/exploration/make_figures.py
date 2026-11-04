#!/usr/bin/env python3
"""
Figures for the progress meeting.

Each figure backs one finding or one open decision:

  01  complementary cumulative distribution of fan-in, with the strata
  02  the four network populations of the zero grid
  03  Spearman correlation of each profile variable with fan-in
  04  share of packages with fan-in, and packages created, per year
  05  monthly distribution of `modified`, with the audit check
  06  eligible and excluded share per stratum
  07  packages per stratum under raw and external fan-in
  08  silhouette by number of clusters

Reads only outputs already written by passes 06 and 07 and by the registry
audit. Every number, titles included, comes from those files. Each figure
carries a footnote stating how it was computed.

Output: figures/*.png
"""
import os
import re
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

PROFILE = "data/06_profile_analysis/profile_table.parquet"
TABLES = "data/06_profile_analysis/tables"
STRATA = "data/07_strata_analysis/strata_table.parquet"
SPLIT = "data/07_strata_analysis/fan_in_split.parquet"
STRATA_MD = "data/07_strata_analysis/strata_report.md"
AUDIT = "data/audit_sample.jsonl"
OUT = "figures"

ORDER = ["0a isolated", "0b consumer", "1-9", "10-99", "100-999", ">=1000"]
LABELS = ["0a\naislados", "0b\nconsumidores", "1–9", "10–99", "100–999", "≥ 1,000"]
DARK, MID, LIGHT, ALERT, GREY = "#1f4e79", "#4f81bd", "#c6d9f0", "#c0392b", "#9aa5b1"
SOURCE = "Fuente: registro npm; lista de referencia del 18-09-2026."

NOTES = {
    "01_distribucion_fan_in": (
        "Distribución acumulada complementaria: proporción de todos los paquetes "
        "con Fan-In mayor o igual a x. Ambos ejes logarítmicos; los paquetes con "
        "Fan-In 0 no se pueden mostrar en esa escala. Franjas: estratos propuestos."),
    "02_poblaciones_de_la_red": (
        "Fan-In y Fan-Out de dependencias de producción, sobre todos los nodos "
        "de la red."),
    "03_correlaciones_con_fan_in": (
        "Correlación de Spearman: de rangos, robusta a valores extremos. Calculada "
        "sobre todos los paquetes con perfil y sobre los que tienen Fan-In > 0."),
    "04_adopcion_y_creacion_por_ano": (
        "Año de creación según el registro. Arriba: porcentaje de paquetes de cada "
        "año con al menos un dependiente de producción."),
    "05_fecha_de_modificacion": (
        "Mes del campo modified del registro. Auditoría: muestra aleatoria con "
        "semilla fija; se compara modified con la publicación de la última versión."),
    "06_elegibles_y_excluidos": (
        "Elegible: con perfil, al menos 365 días al 18-09, no deprecado, no excluido, "
        "y 5 archivos o más publicados, o sin ese dato."),
    "07_fan_in_bruto_y_externo": (
        "Externo: solo dependientes de otro scope. Porcentaje: cambio neto de "
        "paquetes en cada estrato. Eje vertical logarítmico."),
    "08_silueta_por_numero_de_grupos": (
        "k-means sobre log(x+1) de ocho variables de Fan-In y Fan-Out, "
        "estandarizadas; silueta en una muestra aleatoria de 10,000. "
        "Umbrales de Kaufman y Rousseeuw."),
}

plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
})


def save(fig, name):
    width = int(fig.get_figwidth() * 17)
    note = textwrap.fill(NOTES[name], width)
    lines = note.count("\n") + 2
    bottom = min(0.25, (lines * 0.12 + 0.05) / fig.get_figheight())
    fig.text(0.01, 0.01, f"{note}\n{SOURCE}", fontsize=7, color="#555555", va="bottom")
    fig.tight_layout(rect=(0, bottom, 1, 1))
    fig.savefig(os.path.join(OUT, f"{name}.png"), dpi=200)
    plt.close(fig)
    print(f"  {name}.png")


def fmt(n):
    return f"{int(n):,}"


def pct_label(v, _):
    p = v * 100
    if p <= 0:
        return ""
    decimals = max(0, -int(np.floor(np.log10(p))))
    return f"{p:.{decimals}f}%"


def fig_distribution(prof, st):
    fi = prof["fan_in"].to_numpy()
    xs, counts = np.unique(fi[fi >= 1], return_counts=True)
    share = counts[::-1].cumsum()[::-1] / len(fi)
    strata = st["stratum_decade"].value_counts()
    fig, ax = plt.subplots(figsize=(8.5, 5))
    bands = [(1, 10, "1-9"), (10, 100, "10-99"), (100, 1000, "100-999"),
             (1000, xs.max() * 1.5, ">=1000")]
    for i, (lo, hi, key) in enumerate(bands):
        ax.axvspan(lo, hi, color=LIGHT if i % 2 == 0 else "#e9eff7", zorder=0)
        ax.text((lo * hi) ** 0.5, 0.45,
                f"{LABELS[ORDER.index(key)]}\n{fmt(strata.get(key, 0))} paq.",
                ha="center", va="top", fontsize=8)
    ax.loglog(xs, share, color=DARK, lw=1.6, zorder=3)
    ax.set_ylim(share.min() / 2, 0.6)
    ax.set_xlim(1, xs.max() * 1.5)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(FuncFormatter(pct_label))
    ax.set_xlabel("Fan-In (x)")
    ax.set_ylabel("Proporción de paquetes con Fan-In ≥ x")
    ax.set_title(f"El Fan-In tiene cola larga: {(fi == 0).mean() * 100:.1f}% en cero "
                 f"y {int((fi >= 10_000).sum())} paquetes con 10,000 o más")
    save(fig, "01_distribucion_fan_in")


def fig_populations(prof):
    fi0, fo0 = prof["fan_in"] == 0, prof["fan_out"] == 0
    groups = [("Aislados", (fi0 & fo0).mean(), GREY, "white"),
              ("Solo consumen", (fi0 & ~fo0).mean(), LIGHT, "black"),
              ("Solo proveen", (~fi0 & fo0).mean(), MID, "white"),
              ("Intermedios", (~fi0 & ~fo0).mean(), DARK, "white")]
    fig, ax = plt.subplots(figsize=(9, 2.8))
    left = 0.0
    for label, share, color, ink in groups:
        ax.barh(0, share, left=left, color=color, edgecolor="white", height=0.6)
        text = f"{label}\n{share * 100:.1f}%"
        if share > 0.08:
            ax.text(left + share / 2, 0, text, ha="center", va="center",
                    color=ink, fontsize=9)
        else:
            ax.text(left + share / 2, 0.42, text, ha="center", va="bottom", fontsize=9)
        left += share
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, 1.0)
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v * 100:.0f}%"))
    ax.spines["left"].set_visible(False)
    ax.set_title(f"El {fi0.mean() * 100:.1f}% de los paquetes no es usado por ningún otro")
    save(fig, "02_poblaciones_de_la_red")


def fig_correlations():
    t = pd.read_csv(os.path.join(TABLES, "s03_spearman_fanin.csv"))
    t = t.sort_values("rho_fan_in_pos", key=abs)
    profile = t[~t["variable"].str.startswith("fan_")]
    top = profile[["rho_all", "rho_fan_in_pos"]].abs().max().max()
    labels = [v + " (descartada)" if v == "days_since_mod" else v for v in t["variable"]]
    y = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(8, 6.5))
    ax.barh(y - 0.2, t["rho_all"], height=0.4, color=LIGHT, label="Todos los paquetes")
    ax.barh(y + 0.2, t["rho_fan_in_pos"], height=0.4, color=DARK,
            label="Solo con Fan-In > 0")
    ax.axvline(0, color="black", lw=0.6)
    ax.axvline(0.30, ls="--", color=ALERT, lw=1)
    ax.set_ylim(-0.7, len(t) + 0.6)
    ax.text(0.305, len(t) - 0.2, "0.30: asociación moderada", color=ALERT,
            fontsize=8, va="bottom")
    ax.set_yticks(y, labels)
    ax.set_xlabel("Correlación de Spearman con el Fan-In")
    ax.legend(loc="lower right", frameon=False)
    ax.set_title(f"Ninguna variable del perfil supera {top:.2f}; "
                 f"solo otros tipos de Fan-In se acercan a 0.30")
    save(fig, "03_correlaciones_con_fan_in")


def fig_years():
    t = pd.read_csv(os.path.join(TABLES, "s06_by_year.csv"))
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t = t[t["year"].between(2010, 2026)].astype({"year": int})
    n = dict(zip(t["year"], t["n"]))
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True,
                                 gridspec_kw={"height_ratios": [1.2, 1]})
    a1.plot(t["year"], t["pct_fi_pos"], marker="o", color=DARK)
    a1.set_ylabel("% con Fan-In > 0")
    a1.set_title("Los paquetes antiguos se adoptan más; 2024 y 2026 se disparan en creación")
    colors = [ALERT if y in (2024, 2026) else MID for y in t["year"]]
    a2.bar(t["year"], t["n"], color=colors)
    for year in (2024, 2026):
        if year in n and 2023 in n:
            a2.text(year, n[year] * 1.03, f"×{n[year] / n[2023]:.1f} vs 2023",
                    ha="center", fontsize=8, color=ALERT)
    a2.set_ylabel("Paquetes creados")
    a2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1000:,.0f} mil"))
    a2.set_xticks(t["year"])
    a2.tick_params(axis="x", rotation=45)
    a2.text(0.99, 0.95, "2026: hasta octubre", transform=a2.transAxes,
            ha="right", va="top", fontsize=8, color="#555555")
    save(fig, "04_adopcion_y_creacion_por_ano")


def fig_modified():
    m = pd.read_csv(os.path.join(TABLES, "s09_modified_monthly.csv"))
    m["month"] = pd.PeriodIndex(m["month"], freq="M")
    m = m[m["month"] >= pd.Period("2012-01", "M")].sort_values("month")
    window = m["month"].isin([pd.Period(p, "M") for p in ("2022-04", "2022-05", "2022-06")])
    in_window = int(m.loc[window, "n"].sum())

    a = pd.read_json(AUDIT, lines=True)
    a = a[a["status"] == "ok"]
    mod = pd.to_datetime(a["modified"], utc=True, errors="coerce")
    last = pd.to_datetime(a["last_publish"], utc=True, errors="coerce")
    gap = (mod - last).dt.days
    w = mod.between(pd.Timestamp("2022-04-01", tz="UTC"),
                    pd.Timestamp("2022-07-01", tz="UTC"), inclusive="left")
    p_in = (gap[w].dropna() > 30).mean() * 100
    p_out = (gap[~w].dropna() > 30).mean() * 100

    fig, ax = plt.subplots(figsize=(9, 4.3))
    ax.bar(m["month"].dt.to_timestamp(), m["n"], width=25,
           color=[ALERT if x else GREY for x in window])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1000:,.0f} mil"))
    ax.set_ylabel("Paquetes por mes de última modificación")
    ax.set_title(f"{in_window / 1e6:.2f} millones de paquetes figuran modificados "
                 f"entre abril y junio de 2022")
    ax.text(0.01, 0.95,
            f"Auditoría, {len(a):,} paquetes al azar: de los modificados en esa ventana,\n"
            f"{p_in:.1f}% llevaba más de 30 días sin publicar una versión, "
            f"contra {p_out:.1f}% del resto.",
            transform=ax.transAxes, va="top", fontsize=8.5)
    save(fig, "05_fecha_de_modificacion")


def fig_eligible(st):
    g = st.groupby("stratum_decade").agg(n=("name", "size"),
                                         eligible=("eligible", "sum"),
                                         excluded=("excluded", "sum")).reindex(ORDER)
    x = np.arange(len(ORDER))
    w = 0.38
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.bar(x - w / 2, g["eligible"] / g["n"] * 100, w, color=DARK, label="Elegibles")
    ax.bar(x + w / 2, g["excluded"] / g["n"] * 100, w, color=ALERT, label="Excluidos")
    for i, (e, n) in enumerate(zip(g["eligible"], g["n"])):
        ax.text(i - w / 2, e / n * 100 + 1.5, fmt(e), ha="center", fontsize=8)
    ax.set_xticks(x, LABELS)
    ax.set_ylim(0, 100)
    ax.set_ylabel("% del estrato")
    ax.legend(frameon=False)
    ax.set_title(f"Todos los estratos tienen elegibles suficientes: "
                 f"el más chico tiene {fmt(g['eligible'].min())}")
    save(fig, "06_elegibles_y_excluidos")


def fig_external(st, sp):
    d = st[["name", "stratum_decade"]].merge(sp[["name", "stratum_external"]], on="name")
    raw = d["stratum_decade"].value_counts().reindex(ORDER).fillna(0).to_numpy()
    ext = d["stratum_external"].value_counts().reindex(ORDER).fillna(0).to_numpy()
    moved = int((d["stratum_decade"] != d["stratum_external"]).sum())
    x = np.arange(len(ORDER))
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.vlines(x, np.minimum(raw, ext), np.maximum(raw, ext), color=GREY, lw=2, zorder=1)
    ax.scatter(x, raw, s=70, facecolor="white", edgecolor=DARK, lw=1.5,
               label="Fan-In bruto", zorder=2)
    ax.scatter(x, ext, s=70, color=DARK, label="Solo dependientes externos", zorder=3)
    ax.set_yscale("log")
    for i, (r, e) in enumerate(zip(raw, ext)):
        change = (e - r) / r * 100
        ax.text(i + 0.12, (r * e) ** 0.5, f"{change:+.1f}%", va="center", fontsize=8,
                color=ALERT if change < 0 else "#333333")
    ax.set_xticks(x, LABELS)
    ax.set_xlim(-0.5, len(ORDER) - 0.3)
    ax.set_ylabel("Paquetes (escala logarítmica)")
    ax.legend(frameon=False, loc="upper right")
    ax.set_title(f"Contar solo dependientes externos cambia de estrato a {fmt(moved)} paquetes")
    save(fig, "07_fan_in_bruto_y_externo")


def fig_silhouette():
    rows = []
    with open(STRATA_MD, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\|\s*(\d+)\s*\|\s*[\d,]+\s*\|\s*([0-9.]+)\s*\|\s*$", line)
            if m:
                rows.append((int(m.group(1)), float(m.group(2))))
    k, s = zip(*rows)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for low, high, color, label in [(0, 0.25, "#f2f2f2", "Sin estructura"),
                                    (0.25, 0.50, "#fdebd0", "Estructura débil"),
                                    (0.50, 0.70, "#e8f6ef", "Estructura razonable")]:
        ax.axhspan(low, high, color=color, zorder=0)
        ax.text(max(k) + 0.15, (low + high) / 2, label, va="center",
                fontsize=8, color="#555555")
    ax.plot(k, s, marker="o", color=DARK, zorder=3)
    for ki, si in zip(k, s):
        ax.text(ki, si + 0.025, f"{si:.3f}", ha="center", fontsize=8)
    ax.set_xlim(min(k) - 0.5, max(k) + 1.6)
    ax.set_ylim(0, 0.7)
    ax.set_xlabel("Número de grupos (k)")
    ax.set_ylabel("Silueta")
    best = k[int(np.argmax(s))]
    title = ("La silueta sube sin llegar a un máximo: no hay un número natural de grupos"
             if best == max(k) else f"La silueta alcanza su máximo con k = {best}")
    ax.set_title(title)
    save(fig, "08_silueta_por_numero_de_grupos")


def main():
    os.makedirs(OUT, exist_ok=True)
    prof = pd.read_parquet(PROFILE, columns=["fan_in", "fan_out"])
    st = pd.read_parquet(STRATA, columns=["name", "stratum_decade", "excluded", "eligible"])
    sp = pd.read_parquet(SPLIT, columns=["name", "stratum_external"])
    print("Writing figures:")
    fig_distribution(prof, st)
    fig_populations(prof)
    fig_correlations()
    fig_years()
    fig_modified()
    fig_eligible(st)
    fig_external(st, sp)
    fig_silhouette()


if __name__ == "__main__":
    main()