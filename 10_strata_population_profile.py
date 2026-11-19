import json
import time
from datetime import date
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, kruskal, rankdata

BASE = Path(__file__).resolve().parent
INPUT = BASE / "data" / "fanin_population" / "fanin_population.parquet"
STRATA_META = BASE / "data" / "strata_definition" / "run_metadata.json"
STRATA_CONFIG = "6 tramos, con pico"
DIR_OUT = BASE / "data" / "strata_population_profile"
DIR_FIG = DIR_OUT / "figures"
SNAPSHOT_DATE = date(2026, 9, 18)
FAMILY_MIN_SIZE = 2

COLS = ["name", "scope", "scope_size", "created_date", "fan_in", "fan_out",
        "n_versions", "n_maintainers", "n_keywords", "n_peer", "n_opt",
        "deprecated", "has_github"]
NUMERIC = {
    "fan_in": "Fan-In",
    "n_versions": "Versiones",
    "n_maintainers": "Mantenedores",
    "age_years": "Edad (años)",
    "n_keywords": "Palabras clave",
    "n_peer": "Dependencias peer",
    "n_opt": "Dependencias opcionales",
    "fan_out": "Fan-Out (descriptivo)",
}
BINARY = {
    "has_github": "En GitHub",
    "deprecated": "Deprecado",
    "familia": "Familia",
}
CORR_VARS = ["n_versions", "n_maintainers", "age_years", "n_keywords",
             "n_peer", "n_opt", "has_github", "deprecated", "familia"]
LOG_SCALE = {"fan_in", "n_versions", "n_maintainers", "n_keywords",
             "n_peer", "n_opt", "fan_out"}


# Load population and assign strata
def load():
    df = pd.read_parquet(str(INPUT), columns=COLS)
    df = df[df["fan_in"] > 0].reset_index(drop=True)
    days = (pd.Timestamp(SNAPSHOT_DATE)
            - pd.to_datetime(df["created_date"])).dt.days
    df["age_years"] = days / 365.25
    for col in ("has_github", "deprecated"):
        df[col] = df[col].fillna(0).astype(bool).astype(np.int8)
    df["familia"] = (df["scope_size"] >= FAMILY_MIN_SIZE).astype(np.int8)
    with open(str(STRATA_META), encoding="utf-8") as f:
        edges = json.load(f)["edges"][STRATA_CONFIG]
    df["tramo"] = np.searchsorted(np.array(edges), df["fan_in"].values,
                                  side="right")
    return df, edges


# Stratum labels
def labels_for(edges):
    out = []
    for i, lo in enumerate(edges):
        hi = edges[i + 1] - 1 if i + 1 < len(edges) else None
        out.append(f"{lo} o más" if hi is None else f"{lo} a {hi}")
    return out


# Spearman rho
def spearman(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    if m.sum() < 3:
        return np.nan
    rx, ry = rankdata(x[m]), rankdata(y[m])
    dx, dy = rx - rx.mean(), ry - ry.mean()
    den = np.sqrt((dx * dx).sum() * (dy * dy).sum())
    return float((dx * dy).sum() / den) if den > 0 else np.nan


# Descriptives per stratum
def describe(df, n_strata):
    rows = []
    groups = [(t, df[df["tramo"] == t]) for t in range(1, n_strata + 1)]
    groups.append(("Total", df))
    for var in NUMERIC:
        for t, g in groups:
            s = g[var].dropna()
            rows.append({"variable": var, "tramo": t, "n": len(s),
                         "media": s.mean(), "q1": s.quantile(0.25),
                         "mediana": s.median(), "q3": s.quantile(0.75),
                         "max": s.max()})
    for var in BINARY:
        for t, g in groups:
            rows.append({"variable": var, "tramo": t, "n": len(g),
                         "pct_si": 100 * g[var].mean()})
    return pd.DataFrame(rows)


# Kruskal-Wallis, chi-square and trend
def between_strata(df):
    rows = []
    n = len(df)
    for var in NUMERIC:
        if var == "fan_in":
            continue
        samples = [g[var].dropna().values for _, g in df.groupby("tramo")]
        h, p = kruskal(*samples)
        rows.append({"variable": var, "prueba": "Kruskal-Wallis",
                     "estadistico": h, "p": p, "efecto": h / (n - 1),
                     "medida_efecto": "épsilon²",
                     "rho_con_tramo": spearman(df[var], df["tramo"])})
    for var in BINARY:
        tab = pd.crosstab(df["tramo"], df[var])
        chi2, p, _, _ = chi2_contingency(tab)
        k = min(tab.shape) - 1
        rows.append({"variable": var, "prueba": "Chi-cuadrado",
                     "estadistico": chi2, "p": p,
                     "efecto": np.sqrt(chi2 / (n * k)) if k > 0 else np.nan,
                     "medida_efecto": "V de Cramér",
                     "rho_con_tramo": spearman(df[var], df["tramo"])})
    return pd.DataFrame(rows)


# Spearman with Fan-In per stratum
def within_strata(df, n_strata):
    rows = []
    for var in CORR_VARS:
        r = {"variable": var, "poblacion": spearman(df[var], df["fan_in"])}
        for t in range(1, n_strata + 1):
            g = df[df["tramo"] == t]
            r[f"tramo_{t}"] = spearman(g[var], g["fan_in"])
        rows.append(r)
    return pd.DataFrame(rows)


# Boxplots per stratum
def fig_boxplots(df, labels):
    vars_ = [v for v in NUMERIC if v != "fan_in"]
    ncol = 3
    nrow = int(np.ceil(len(vars_) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(5 * ncol, 3.6 * nrow))
    for ax, var in zip(axes.flat, vars_):
        data = [g[var].dropna().values for _, g in df.groupby("tramo")]
        if var in LOG_SCALE:
            data = [np.log10(d + 1) for d in data]
        ax.boxplot(data, showfliers=False)
        ax.set_xticks(range(1, len(labels) + 1))
        ax.set_xticklabels(labels, rotation=30, fontsize=8)
        ax.set_title(NUMERIC[var] + (" — log10(x+1)" if var in LOG_SCALE else ""),
                     fontsize=10)
    for ax in list(axes.flat)[len(vars_):]:
        ax.axis("off")
    fig.suptitle("Variables de perfil por tramo de Fan-In (sin atípicos)")
    fig.tight_layout()
    fig.savefig(str(DIR_FIG / "boxplots_por_tramo.png"), dpi=150)
    plt.close(fig)


# Yes/no shares per stratum
def fig_binary(desc, labels):
    fig, ax = plt.subplots(figsize=(8, 4))
    w = 0.8 / len(BINARY)
    x = np.arange(len(labels))
    for i, (var, lab) in enumerate(BINARY.items()):
        d = desc[(desc["variable"] == var) & (desc["tramo"] != "Total")]
        ax.bar(x + i * w - 0.4 + w / 2, d["pct_si"].values, w, label=lab)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30)
    ax.set_ylabel("% de paquetes")
    ax.set_xlabel("Tramo de Fan-In")
    ax.legend()
    fig.tight_layout()
    fig.savefig(str(DIR_FIG / "binarias_por_tramo.png"), dpi=150)
    plt.close(fig)


# Correlation heatmap
def fig_heatmap(within, labels):
    cols = ["poblacion"] + [c for c in within.columns if c.startswith("tramo_")]
    m = within[cols].values.astype(float)
    fig, ax = plt.subplots(figsize=(1.3 * len(cols) + 2, 0.5 * len(within) + 1.5))
    im = ax.imshow(m, cmap="RdBu_r", vmin=-0.5, vmax=0.5, aspect="auto")
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(["Población"] + labels, rotation=30)
    ax.set_yticks(range(len(within)))
    ax.set_yticklabels([NUMERIC.get(v, BINARY.get(v, v)) for v in within["variable"]])
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            if not np.isnan(m[i, j]):
                ax.text(j, i, f"{m[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, label="ρ de Spearman con Fan-In")
    ax.set_title("Correlación con Fan-In: población y dentro de cada tramo")
    fig.tight_layout()
    fig.savefig(str(DIR_FIG / "spearman_dentro_de_tramos.png"), dpi=150)
    plt.close(fig)


# Number formatting
def f(v, d=1):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fp(p):
    return "< 0,001" if p < 0.001 else f(p, 3)


# Write results.md
def write_md(path, df, edges, labels, desc, between, within):
    n = len(df)
    sizes = df["tramo"].value_counts().sort_index()
    with open(str(path), "w", encoding="utf-8") as fh:
        w = fh.write
        w("# Estadísticos de la población por tramo de Fan-In\n\n")
        w(f"Generado: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        w("## Entradas\n\n")
        w(f"- Población: `{INPUT.relative_to(BASE)}` (G1, Fan-In del registro), "
          f"{f(n, 0)} paquetes\n")
        w(f"- Tramos: {STRATA_CONFIG} (límites {', '.join(map(str, edges))})\n")
        w(f"- Edad: años entre la creación y el {SNAPSHOT_DATE.isoformat()}\n")
        w(f"- Familia: `scope_size >= {FAMILY_MIN_SIZE}`\n")
        w("- No se usan las dependencias de desarrollo. El Fan-Out es solo descriptivo.\n\n")

        w("## 1. Tamaño de los tramos\n\n| Tramo | Fan-In | Paquetes | % |\n|---|---|---|---|\n")
        for t, c in sizes.items():
            w(f"| {t} | {labels[t - 1]} | {f(c, 0)} | {f(100 * c / n)} % |\n")
        w(f"| Total | | {f(n, 0)} | 100,0 % |\n\n")

        w("## 2. Descriptivos por tramo\n\n")
        for var, lab in NUMERIC.items():
            d = desc[desc["variable"] == var]
            w(f"### {lab}\n\n| Tramo | Media | Q1 | Mediana | Q3 | Máximo |\n"
              "|---|---|---|---|---|---|\n")
            for r in d.itertuples():
                name = r.tramo if r.tramo == "Total" else f"{r.tramo} ({labels[r.tramo - 1]})"
                w(f"| {name} | {f(r.media)} | {f(r.q1)} | {f(r.mediana)} | "
                  f"{f(r.q3)} | {f(r.max)} |\n")
            w("\n")
        w("### Variables sí/no (% de paquetes con sí)\n\n| Tramo | "
          + " | ".join(BINARY.values()) + " |\n|---|" + "---|" * len(BINARY) + "\n")
        for t in list(range(1, len(edges) + 1)) + ["Total"]:
            name = t if t == "Total" else f"{t} ({labels[t - 1]})"
            vals = [desc[(desc["variable"] == v) & (desc["tramo"] == t)]["pct_si"].iloc[0]
                    for v in BINARY]
            w(f"| {name} | " + " | ".join(f(v) + " %" for v in vals) + " |\n")
        w("\n![Boxplots](figures/boxplots_por_tramo.png)\n\n")
        w("![Variables sí/no](figures/binarias_por_tramo.png)\n\n")

        w("## 3. Diferencias entre tramos\n\n")
        w("Con cientos de miles de paquetes casi cualquier diferencia es "
          "significativa, así que se interpreta el tamaño del efecto. "
          "Épsilon² (Kruskal-Wallis) y V de Cramér van de 0 a 1. "
          "ρ con tramo: tendencia de la variable al subir de tramo (1 a 6).\n\n")
        w("| Variable | Prueba | Estadístico | p | Efecto | Medida | ρ con tramo |\n"
          "|---|---|---|---|---|---|---|\n")
        for r in between.itertuples():
            lab = NUMERIC.get(r.variable, BINARY.get(r.variable, r.variable))
            w(f"| {lab} | {r.prueba} | {f(r.estadistico)} | {fp(r.p)} | "
              f"{f(r.efecto, 3)} | {r.medida_efecto} | {f(r.rho_con_tramo, 3)} |\n")
        w("\n")

        w("## 4. Correlación con Fan-In, en la población y dentro de cada tramo\n\n")
        w("ρ de Spearman. Dentro de un tramo el rango de Fan-In es angosto, por lo "
          "que las correlaciones tienden a ser menores que en la población "
          "completa (restricción de rango); no indican por sí solas una relación "
          "más débil.\n\n")
        w("| Variable | Población | " + " | ".join(f"Tramo {i + 1}" for i in range(len(edges)))
          + " |\n|---|---|" + "---|" * len(edges) + "\n")
        for r in within.to_dict("records"):
            lab = NUMERIC.get(r["variable"], BINARY.get(r["variable"], r["variable"]))
            w(f"| {lab} | {f(r['poblacion'], 3)} | "
              + " | ".join(f(r[f'tramo_{i + 1}'], 3) for i in range(len(edges))) + " |\n")
        w("\n![Correlaciones](figures/spearman_dentro_de_tramos.png)\n")


# Population statistics
def main():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Loading {INPUT} ...")
    df, edges = load()
    labels = labels_for(edges)
    n_strata = len(edges)
    print(f"  packages: {len(df):,}; strata: {edges}")
    DIR_FIG.mkdir(parents=True, exist_ok=True)

    print("Descriptives ...")
    desc = describe(df, n_strata)
    print("Differences between strata ...")
    between = between_strata(df)
    print("Correlations with Fan-In ...")
    within = within_strata(df, n_strata)
    print("Figures ...")
    fig_boxplots(df, labels)
    fig_binary(desc, labels)
    fig_heatmap(within, labels)

    desc.to_csv(DIR_OUT / "descriptives.csv", index=False, encoding="utf-8")
    between.to_csv(DIR_OUT / "between_strata.csv", index=False, encoding="utf-8")
    within.to_csv(DIR_OUT / "within_strata_spearman.csv", index=False, encoding="utf-8")
    write_md(DIR_OUT / "results.md", df, edges, labels, desc, between, within)
    with open(str(DIR_OUT / "run_metadata.json"), "w", encoding="utf-8") as fh:
        json.dump({"executed_at": started, "input": str(INPUT),
                   "strata_config": STRATA_CONFIG, "edges": edges,
                   "n_packages": int(len(df)),
                   "snapshot_date": SNAPSHOT_DATE.isoformat(),
                   "numeric": list(NUMERIC), "binary": list(BINARY),
                   "correlated_with_fan_in": CORR_VARS},
                  fh, indent=2, ensure_ascii=False)
    print(f"Done. Results in {DIR_OUT}")


if __name__ == "__main__":
    main()
