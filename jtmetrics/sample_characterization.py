import json
import time
import warnings
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, kruskal, spearmanr
from sample_metrics import GROUPS, SAMPLE, STRATA_CONFIG, STRATA_META, labels_for

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
DIR_OUT = BASE / "data" / "strata_jtmetrics_characterization"
DIR_FIG = DIR_OUT / "figures"

QUALITY = ["parse_errors", "traverse_errors"]
STRUCT = {g: ms for g, ms in GROUPS.items() if not set(ms) <= set(QUALITY)}
METRICS = [m for ms in STRUCT.values() for m in ms]
LABELS = {
    "n_files": "Cantidad de archivos",
    "loc": "Líneas de código totales",
    "loc_file_mean": "Líneas por archivo (media)",
    "loc_file_max": "Líneas del archivo más largo",
    "n_functions": "Cantidad de funciones",
    "n_classes": "Cantidad de clases",
    "n_methods": "Cantidad de métodos",
    "func_length_mean": "Largo de las funciones (media)",
    "func_length_median": "Largo de las funciones (mediana)",
    "func_length_max": "Largo de la función más larga",
    "params_mean": "Parámetros por función (media)",
    "params_max": "Parámetros de la función con más parámetros",
    "file_edges": "Importaciones internas totales",
    "edges_per_file": "Importaciones por archivo",
    "density": "Densidad de importaciones",
    "coupled_files_pct": "% de archivos conectados",
    "max_fan_in": "Importaciones recibidas por el archivo más importado",
    "max_fan_out": "Importaciones hechas por el archivo que más importa",
    "components": "Grupos de archivos desconectados",
    "largest_component_pct": "% de archivos en el grupo más grande",
    "cyclic_files_pct": "% de archivos en ciclos de importación",
    "instability_mean": "Inestabilidad media",
    "stable_pct": "% de archivos estables",
    "unstable_pct": "% de archivos inestables",
    "centrality_max": "Centralidad del archivo más central",
    "func_fan_in_mean": "Llamadas recibidas por función (media)",
    "func_fan_out_mean": "Llamadas hechas por función (media)",
    "func_dep_score_mean": "Puntaje de dependencia por función (media)",
    "func_coupled_pct": "% de funciones conectadas",
    "class_fan_in_mean": "Llamadas recibidas por clase (media)",
    "class_fan_out_mean": "Llamadas hechas por clase (media)",
    "class_dep_score_mean": "Puntaje de dependencia por clase (media)",
}
CONTROL_MIN_FILES = 3
SIZE_BINS = [-np.inf, 35, 500, 5000, np.inf]
SIZE_TYPES = ["Micro (≤ 35 líneas)", "Pequeño (36 a 500)", "Mediano (501 a 5.000)", "Grande (> 5.000)"]
STRUCT_TYPES = ["Un solo archivo", "Varios archivos sin importaciones",
                "Conectado sin ciclos", "Conectado con ciclos"]
CONCENTRATION = ["loc", "n_files", "n_functions", "n_classes", "file_edges"]
TOP_PCT = [10, 1]
STRATA_COLORS = ["#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
STRUCT_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
SIZE_COLORS = ["#cde2fb", "#6da7ec", "#256abf", "#0d366b"]


# Weighted quantile from the weighted cumulative distribution
def wquantile(x, w, q):
    if len(x) == 0:
        return np.nan
    o = np.argsort(x, kind="stable")
    x, w = x[o], w[o]
    cw = np.cumsum(w) / w.sum()
    return float(x[min(np.searchsorted(cw, q), len(x) - 1)])


# Share of the weighted total held by the largest packages
def top_share(x, w, pct):
    if (w * x).sum() == 0:
        return np.nan
    o = np.argsort(-x, kind="stable")
    x, w = x[o], w[o]
    wn = w / w.sum()
    prev = np.cumsum(wn) - wn
    f = np.clip((pct / 100 - prev) / wn, 0, 1)
    return float(100 * (f * w * x).sum() / (w * x).sum())


def cramers_v(a, b):
    tab = pd.crosstab(a, b)
    if min(tab.shape) < 2:
        return np.nan
    chi2 = chi2_contingency(tab)[0]
    return float(np.sqrt(chi2 / (tab.to_numpy().sum() * (min(tab.shape) - 1))))


def spearman(a, b):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return float(spearmanr(a, b)[0])


def pct_w(df, mask):
    return 100 * df.loc[mask, "w"].sum() / df["w"].sum()


# Sample with population weights and package types
def load():
    with open(str(STRATA_META), encoding="utf-8") as f:
        edges = json.load(f)["edges"][STRATA_CONFIG]
    df = pd.read_csv(str(SAMPLE / "package_metrics.csv"))
    alloc = pd.read_csv(str(SAMPLE / "allocation.csv")).set_index("tramo")
    n_h = df.groupby("tramo").size()
    df["w"] = df["tramo"].map(alloc["N_h"] / n_h)
    df["structure"] = np.select(
        [df["n_files"] == 1, df["file_edges"] == 0, df["cyclic_files_pct"] > 0],
        [STRUCT_TYPES[0], STRUCT_TYPES[1], STRUCT_TYPES[3]], default=STRUCT_TYPES[2])
    df["size"] = pd.cut(df["loc"], SIZE_BINS, labels=SIZE_TYPES).astype(str)
    return df, labels_for(edges), alloc


# RQ1: weighted profile of every metric
def profile(df):
    rows = []
    for g, ms in STRUCT.items():
        for m in ms:
            ok = df[m].notna()
            x, w = df.loc[ok, m].to_numpy(float), df.loc[ok, "w"].to_numpy(float)
            rows.append({"group": g, "metric": m, "label": LABELS[m], "n": int(ok.sum()),
                         "pct_defined": pct_w(df, ok), "q1": wquantile(x, w, .25),
                         "median": wquantile(x, w, .5), "q3": wquantile(x, w, .75),
                         "mean": float(np.average(x, weights=w)), "p90": wquantile(x, w, .9),
                         "pct_zero": 100 * w[x == 0].sum() / w.sum(),
                         "median_unweighted": float(np.median(x))})
    return pd.DataFrame(rows)


# RQ1: key cases, weighted total and per stratum
def key_cases(df):
    cases = {
        "Un solo archivo": df["n_files"] == 1,
        "Sin importaciones internas": df["file_edges"] == 0,
        "Con al menos un ciclo de importación": df["cyclic_files_pct"] > 0,
        "Sin funciones": df["n_functions"] == 0,
        "Sin clases": df["n_classes"] == 0,
        "Con archivos .d.ts": df["dts_files"] > 0,
        "Con archivos .min.js": df["min_js_files"] > 0,
        "Con errores de parseo": df["parse_errors"] > 0,
        "Con errores de recorrido": df["traverse_errors"] > 0,
    }
    rows = []
    for name, mask in cases.items():
        r = {"case": name, "total_weighted": pct_w(df, mask)}
        for t, g in df.groupby("tramo"):
            r[f"tramo_{t}"] = 100 * mask[g.index].mean()
        r["cramers_v"] = cramers_v(df["tramo"], mask)
        rows.append(r)
    return pd.DataFrame(rows)


# RQ2: quartiles per stratum
def by_stratum(df, subset):
    rows = []
    for m in METRICS:
        for t, g in df.groupby("tramo"):
            v = g[m].dropna()
            rows.append({"subset": subset, "metric": m, "tramo": t, "n": len(v), "q1": v.quantile(.25),
                         "median": v.median(), "q3": v.quantile(.75), "mean": v.mean()})
    return pd.DataFrame(rows)


# RQ2: Kruskal-Wallis epsilon², trend with stratum and Bonferroni p
def effects(df, subset):
    rows = []
    for m in METRICS:
        s = df[["tramo", m]].dropna()
        groups = [g[m].to_numpy() for _, g in s.groupby("tramo")]
        try:
            h, p = kruskal(*groups)
        except ValueError:
            h, p = np.nan, np.nan
        rows.append({"subset": subset, "metric": m, "n": len(s),
                     "eps2": h / (len(s) - 1) if len(s) > 1 else np.nan,
                     "rho": spearman(s["tramo"], s[m]), "p": p})
    out = pd.DataFrame(rows)
    out["p_bonferroni"] = (out["p"] * out["p"].notna().sum()).clip(upper=1)
    return out


# RQ3: mean vs median and share explained by stratum
def variation(prof, eff):
    v = prof[["group", "metric", "label", "median", "mean"]].merge(eff[["metric", "eps2"]], on="metric")
    v["mean_over_median"] = np.where(v["median"] > 0, v["mean"] / v["median"], np.nan)
    v["pct_explained_by_stratum"] = 100 * v["eps2"]
    return v


# RQ3: share of the total held by the largest packages
def concentration(df):
    rows = []
    for m in CONCENTRATION:
        x, w = df[m].to_numpy(float), df["w"].to_numpy(float)
        r = {"metric": m, "label": LABELS[m]}
        for p in TOP_PCT:
            r[f"top_{p}_pct"] = top_share(x, w, p)
        rows.append(r)
    return pd.DataFrame(rows)


# RQ4: share of each package type, weighted total and per stratum
def type_table(df, col, order):
    rows = []
    for k in order:
        mask = df[col] == k
        r = {"dimension": col, "type": k, "n": int(mask.sum()), "total_weighted": pct_w(df, mask)}
        for t, g in df.groupby("tramo"):
            r[f"tramo_{t}"] = 100 * (g[col] == k).mean()
        rows.append(r)
    return pd.DataFrame(rows)


def type_tests(df):
    size_code = df["size"].map({k: i for i, k in enumerate(SIZE_TYPES)})
    return {"structure": {"cramers_v": cramers_v(df["tramo"], df["structure"])},
            "size": {"cramers_v": cramers_v(df["tramo"], df["size"]),
                     "rho": spearman(df["tramo"], size_code)}}


def cross_types(df):
    tab = pd.crosstab(df["structure"], df["size"], values=df["w"], aggfunc="sum", normalize="all")
    return (100 * tab).reindex(index=STRUCT_TYPES, columns=SIZE_TYPES).fillna(0)


# Cumulative distribution of every metric per stratum
def fig_distributions(df, labels, path):
    ncol = 4
    nrow = int(np.ceil(len(METRICS) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.4 * ncol, 3.0 * nrow))
    for ax, m in zip(axes.flat, METRICS):
        for t, g in df.groupby("tramo"):
            v = np.sort(g[m].dropna().to_numpy(float))
            if len(v):
                ax.step(v, np.arange(1, len(v) + 1) / len(v), where="post",
                        color=STRATA_COLORS[t - 1], lw=1.4)
        allv = df[m].dropna()
        if len(allv) and allv.max() > 50 * max(allv.median(), 1):
            ax.set_xscale("symlog", linthresh=1)
        ax.set_title(LABELS[m], fontsize=9, loc="left")
        ax.set_ylim(0, 1.02)
        ax.grid(color="#e6e5e1", lw=0.6)
        ax.tick_params(labelsize=8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    for ax in list(axes.flat)[len(METRICS):]:
        ax.axis("off")
    handles = [plt.Line2D([], [], color=c, lw=2) for c in STRATA_COLORS]
    fig.legend(handles, [f"Tramo {i + 1} ({lab})" for i, lab in enumerate(labels)],
               loc="upper center", ncol=6, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 0.985))
    fig.suptitle("Distribución acumulada de cada métrica por tramo de Fan-In", y=0.998, fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fig.savefig(str(path), dpi=150)
    plt.close(fig)


def stacked(ax, table, order, colors, title, labels):
    rows = ["Total (ponderado)"] + [f"Tramo {i + 1} ({lab})" for i, lab in enumerate(labels)]
    cols = ["total_weighted"] + [f"tramo_{i + 1}" for i in range(len(labels))]
    y = np.arange(len(rows))[::-1]
    left = np.zeros(len(rows))
    for k, c in zip(order, colors):
        vals = table.set_index("type").loc[k, cols].to_numpy(float)
        ax.barh(y, vals, left=left, color=c, edgecolor="white", lw=1.5, height=0.7)
        dark = c in ("#2a78d6", "#256abf", "#0d366b", "#eb6834")
        for yi, l, v in zip(y, left, vals):
            if v >= 6:
                ax.text(l + v / 2, yi, f"{v:.0f}%", ha="center", va="center", fontsize=8,
                        color="white" if dark else "#0b0b0b")
        left += vals
    ax.set_yticks(y, rows, fontsize=9)
    ax.set_xlim(0, 100)
    ax.set_title(title, loc="left", fontsize=11)
    ax.legend(handles=[Patch(color=c, label=k) for k, c in zip(order, colors)], ncol=4,
              loc="upper center", bbox_to_anchor=(0.5, -0.08), frameon=False, fontsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# Package types per stratum as stacked bars
def fig_types(types, labels, path):
    fig, axes = plt.subplots(2, 1, figsize=(11, 8.5))
    stacked(axes[0], types[types["dimension"] == "structure"], STRUCT_TYPES, STRUCT_COLORS,
            "Estructura", labels)
    stacked(axes[1], types[types["dimension"] == "size"], SIZE_TYPES, SIZE_COLORS,
            "Tamaño (líneas de código)", labels)
    fig.suptitle("Tipos de paquete por tramo de Fan-In (% de paquetes)", fontsize=13, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(str(path), dpi=150)
    plt.close(fig)


def num(v, d=None):
    if v is None or pd.isna(v):
        return "—"
    if d is None:
        a = abs(v)
        d = 0 if a >= 100 or float(v).is_integer() else 1 if a >= 10 else 2
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pval(p):
    return "—" if pd.isna(p) else "< 0,001" if p < 0.001 else num(p, 3)


def stratum_cols(labels):
    return " | ".join(f"T{i + 1}" for i in range(len(labels)))


# Medians per stratum with effect sizes, one table per group
def write_rq2_tables(f, strat, eff, labels):
    for g, ms in STRUCT.items():
        f.write(f"#### {g}\n\n| Métrica | {stratum_cols(labels)} | ε² | ρ | p ajustado |\n"
                f"|---|{'---|' * len(labels)}---|---|---|\n")
        for m in ms:
            med = strat[strat["metric"] == m].set_index("tramo")["median"]
            e = eff[eff["metric"] == m].iloc[0]
            f.write(f"| {LABELS[m]} | " + " | ".join(num(med.get(t + 1)) for t in range(len(labels)))
                    + f" | {num(e['eps2'], 3)} | {num(e['rho'], 2)} | {pval(e['p_bonferroni'])} |\n")
        f.write("\n")


# Write results.md
def write_md(path, df, labels, alloc, prof, cases, strat, eff, var, conc, types, tests, cross, control):
    n_t = len(labels)
    with open(str(path), "w", encoding="utf-8") as f:
        f.write("# Caracterización de la muestra JTMetrics\n\n")
        f.write(f"Generado: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n## Entradas\n\n")
        f.write(f"- Muestra: `{(SAMPLE / 'package_metrics.csv').relative_to(BASE)}`, "
                f"{num(len(df), 0)} paquetes en {n_t} tramos ({STRATA_CONFIG})\n")
        f.write(f"- Métricas: {len(METRICS)} métricas de estructura; los errores de JTMetrics se "
                "reportan como casos clave\n")
        f.write(f"- Total ponderado: cada paquete pesa N_h / n_h según su tramo, así el total representa "
                f"a los {num(alloc['N_h'].sum(), 0)} paquetes de la población. Los valores por tramo "
                "no se ponderan\n")
        f.write("- Definida en: % de paquetes donde la métrica se puede calcular (por ejemplo, la "
                "inestabilidad solo existe si hay importaciones internas)\n")
        f.write("- ε²: Kruskal-Wallis, parte de la variación (en rangos) que explica el tramo, de 0 a 1. "
                "ρ: Spearman con el número de tramo. p ajustado: Bonferroni por la cantidad de métricas\n\n")
        f.write("| Tramo | Fan-In | Población | Muestra | Peso por paquete |\n|---|---|---|---|---|\n")
        for t in range(1, n_t + 1):
            f.write(f"| {t} | {labels[t - 1]} | {num(alloc.loc[t, 'N_h'], 0)} | "
                    f"{num((df['tramo'] == t).sum(), 0)} | {num(df.loc[df['tramo'] == t, 'w'].iloc[0], 1)} |\n")

        f.write("\n## RQ1. ¿Cómo es por dentro un paquete npm con dependientes?\n\n### Casos clave\n\n")
        f.write(f"| Caso | Total (ponderado) | {stratum_cols(labels)} | V de Cramér |\n"
                f"|---|---|{'---|' * n_t}---|\n")
        for r in cases.itertuples(index=False):
            f.write(f"| {r.case} | {num(r.total_weighted, 1)} % | "
                    + " | ".join(f"{num(getattr(r, f'tramo_{t}'), 1)} %" for t in range(1, n_t + 1))
                    + f" | {num(r.cramers_v, 3)} |\n")
        f.write("\n### Métricas (total ponderado)\n\n")
        for g, ms in STRUCT.items():
            f.write(f"#### {g}\n\n| Métrica | Definida en | Q1 | Mediana | Q3 | Media | P90 | % en 0 |\n"
                    "|---|---|---|---|---|---|---|---|\n")
            for r in prof[prof["group"] == g].itertuples(index=False):
                f.write(f"| {r.label} | {num(r.pct_defined, 1)} % | {num(r.q1)} | {num(r.median)} | "
                        f"{num(r.q3)} | {num(r.mean)} | {num(r.p90)} | {num(r.pct_zero, 1)} % |\n")
            f.write("\n")

        f.write("## RQ2. ¿Cambia según el tramo de Fan-In?\n\n### Todos los paquetes (medianas)\n\n")
        write_rq2_tables(f, strat[strat["subset"] == "todos"], eff[eff["subset"] == "todos"], labels)
        n_c = control.groupby("tramo").size().reindex(range(1, n_t + 1), fill_value=0)
        f.write(f"### Control: {CONTROL_MIN_FILES} o más archivos con al menos una importación interna "
                "(medianas)\n\n")
        f.write(f"Paquetes: {num(len(control), 0)} (" + ", ".join(
            f"T{t}: {n_c[t]}" for t in range(1, n_t + 1)) + "). Sirve para ver si el resultado se "
                "mantiene cuando las métricas tienen margen para variar.\n\n")
        write_rq2_tables(f, strat[strat["subset"] == "control"], eff[eff["subset"] == "control"], labels)

        f.write("## RQ3. ¿Cuánto varían los paquetes entre sí?\n\n### Media, mediana y efecto del tramo\n\n")
        f.write("Media y mediana ponderadas. Una media muy por encima de la mediana indica que unos pocos "
                "paquetes la inflan. El % explicado por el tramo es ε² × 100; el resto de la variación "
                "ocurre dentro de los tramos.\n\n")
        f.write("| Métrica | Mediana | Media | Media / mediana | % explicado por el tramo |\n"
                "|---|---|---|---|---|\n")
        for r in var.itertuples(index=False):
            f.write(f"| {r.label} | {num(r.median)} | {num(r.mean)} | {num(r.mean_over_median)} | "
                    f"{num(r.pct_explained_by_stratum, 2)} % |\n")
        f.write("\n### Concentración en los paquetes más grandes (ponderada)\n\n"
                "| Métrica | % del total en el 10 % más grande | % del total en el 1 % más grande |\n"
                "|---|---|---|\n")
        for r in conc.itertuples(index=False):
            f.write(f"| {r.label} | {num(r.top_10_pct, 1)} % | {num(r.top_1_pct, 1)} % |\n")

        f.write("\n## RQ4. ¿Qué tipos de paquete hay?\n\n")
        for dim, title in (("structure", "Estructura"), ("size", "Tamaño (líneas de código)")):
            f.write(f"### {title}\n\n| Tipo | Total (ponderado) | {stratum_cols(labels)} |\n"
                    f"|---|---|{'---|' * n_t}\n")
            for r in types[types["dimension"] == dim].itertuples(index=False):
                f.write(f"| {r.type} | {num(r.total_weighted, 1)} % | "
                        + " | ".join(f"{num(getattr(r, f'tramo_{t}'), 1)} %" for t in range(1, n_t + 1))
                        + " |\n")
            line = f"\nV de Cramér con el tramo: {num(tests[dim]['cramers_v'], 3)}"
            if "rho" in tests[dim]:
                line += f"; ρ con el tramo: {num(tests[dim]['rho'], 3)}"
            f.write(line + "\n\n")
        f.write("### Estructura por tamaño (% del total ponderado)\n\n| Estructura | "
                + " | ".join(SIZE_TYPES) + " |\n|---|" + "---|" * len(SIZE_TYPES) + "\n")
        for k, row in cross.iterrows():
            f.write(f"| {k} | " + " | ".join(f"{num(v, 1)} %" for v in row) + " |\n")
        f.write("\n![Tipos](figures/types_by_stratum.png)\n\n"
                "![Distribuciones](figures/distributions_by_stratum.png)\n")


# Characterization of the JTMetrics sample
def main():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    if not (SAMPLE / "package_metrics.csv").exists():
        raise SystemExit(f"{SAMPLE / 'package_metrics.csv'} not found. Run jtmetrics/sample_metrics.py first.")
    df, labels, alloc = load()
    DIR_FIG.mkdir(parents=True, exist_ok=True)
    control = df[(df["n_files"] >= CONTROL_MIN_FILES) & (df["file_edges"] >= 1)]

    prof = profile(df)
    cases = key_cases(df)
    strat = pd.concat([by_stratum(df, "todos"), by_stratum(control, "control")], ignore_index=True)
    eff = pd.concat([effects(df, "todos"), effects(control, "control")], ignore_index=True)
    var = variation(prof, eff[eff["subset"] == "todos"])
    conc = concentration(df)
    types = pd.concat([type_table(df, "structure", STRUCT_TYPES), type_table(df, "size", SIZE_TYPES)],
                      ignore_index=True)
    tests = type_tests(df)
    cross = cross_types(df)

    prof.to_csv(str(DIR_OUT / "rq1_profile.csv"), index=False, encoding="utf-8")
    cases.to_csv(str(DIR_OUT / "rq1_key_cases.csv"), index=False, encoding="utf-8")
    strat.to_csv(str(DIR_OUT / "rq2_by_stratum.csv"), index=False, encoding="utf-8")
    eff.to_csv(str(DIR_OUT / "rq2_effects.csv"), index=False, encoding="utf-8")
    var.to_csv(str(DIR_OUT / "rq3_variation.csv"), index=False, encoding="utf-8")
    conc.to_csv(str(DIR_OUT / "rq3_concentration.csv"), index=False, encoding="utf-8")
    types.to_csv(str(DIR_OUT / "rq4_types.csv"), index=False, encoding="utf-8")
    cross.to_csv(str(DIR_OUT / "rq4_structure_by_size.csv"), encoding="utf-8")

    fig_distributions(df, labels, DIR_FIG / "distributions_by_stratum.png")
    fig_types(types, labels, DIR_FIG / "types_by_stratum.png")
    write_md(DIR_OUT / "results.md", df, labels, alloc, prof, cases, strat, eff, var, conc, types,
             tests, cross, control)
    with open(str(DIR_OUT / "run_metadata.json"), "w", encoding="utf-8") as f:
        json.dump({"executed_at": started, "input": str(SAMPLE / "package_metrics.csv"),
                   "strata_config": STRATA_CONFIG, "packages": int(len(df)),
                   "control_packages": int(len(control)), "control_min_files": CONTROL_MIN_FILES,
                   "size_bins": [b for b in SIZE_BINS if np.isfinite(b)], "metrics": METRICS},
                  f, indent=2, ensure_ascii=False)
    print(f"Done. {len(df)} packages, {len(control)} in control. Results in {DIR_OUT}")


if __name__ == "__main__":
    main()
