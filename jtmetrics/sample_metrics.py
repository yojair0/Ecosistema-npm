import gzip
import json
import math
import time
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
STRATA_META = BASE / "data" / "strata_definition" / "run_metadata.json"
STRATA_CONFIG = "6 tramos, con pico"
SAMPLE = BASE / "data" / "strata_jtmetrics_sample"
CONTEXT = ["name", "tramo", "fan_in", "familia", "coverage", "dts_files", "min_js_files", "raw_file"]

GROUPS = {
    "Volumen": ["n_files", "loc", "loc_file_mean", "loc_file_max", "n_functions", "n_classes",
                "n_methods", "func_length_mean", "func_length_median", "func_length_max",
                "params_mean", "params_max"],
    "Acoplamiento entre archivos": ["file_edges", "edges_per_file", "density", "coupled_files_pct",
                                    "max_fan_in", "max_fan_out", "components",
                                    "largest_component_pct", "cyclic_files_pct"],
    "Inestabilidad": ["instability_mean", "stable_pct", "unstable_pct"],
    "Centralidad": ["centrality_max"],
    "Funciones y clases (secundarias)": ["func_fan_in_mean", "func_fan_out_mean",
                                         "func_dep_score_mean", "func_coupled_pct",
                                         "class_fan_in_mean", "class_fan_out_mean",
                                         "class_dep_score_mean"],
    "Calidad de la medición": ["parse_errors", "traverse_errors"],
}
METRICS = [m for ms in GROUPS.values() for m in ms]
BOXPLOT = ["n_files", "loc", "edges_per_file", "coupled_files_pct", "density",
           "largest_component_pct", "cyclic_files_pct", "instability_mean", "centrality_max"]
LOG_SCALE = {"n_files", "loc"}


def obj(x):
    return x if isinstance(x, dict) else {}


def nan_mean(v):
    return float(np.mean(v)) if len(v) else np.nan


def nan_max(v):
    return float(np.max(v)) if len(v) else np.nan


# Number of entries per file
def count_entries(per_file, files):
    total = 0
    for f in files:
        x = per_file.get(f)
        if isinstance(x, (list, dict)):
            total += len(x)
    return total


# Internal import graph among analysed files
def import_graph(coupling, files):
    fs = set(files)
    out = {f: set() for f in files}
    for f in files:
        for dep in obj(coupling.get(f)).get("fanOut", []) or []:
            if dep in fs and dep != f:
                out[f].add(dep)
    inn = {f: set() for f in files}
    for f, deps in out.items():
        for d in deps:
            inn[d].add(f)
    return out, inn


# Weakly connected components (sizes)
def components(out, inn):
    seen, sizes = set(), []
    for start in out:
        if start in seen:
            continue
        stack, size = [start], 0
        seen.add(start)
        while stack:
            v = stack.pop()
            size += 1
            for w in out[v] | inn[v]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        sizes.append(size)
    return sizes


# Files inside import cycles (strongly connected components of size > 1), iterative Tarjan
def cyclic_files(out):
    index, low, on, stack, idx, result = {}, {}, set(), [], [0], 0
    for root in out:
        if root in index:
            continue
        work = [(root, iter(out[root]))]
        index[root] = low[root] = idx[0]; idx[0] += 1
        stack.append(root); on.add(root)
        while work:
            v, it = work[-1]
            nxt = next(it, None)
            if nxt is not None:
                if nxt not in index:
                    index[nxt] = low[nxt] = idx[0]; idx[0] += 1
                    stack.append(nxt); on.add(nxt)
                    work.append((nxt, iter(out[nxt])))
                elif nxt in on:
                    low[v] = min(low[v], index[nxt])
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop(); on.discard(w); comp.append(w)
                    if w == v:
                        break
                if len(comp) > 1:
                    result += len(comp)
    return result


# All package metrics from one raw file
def package_row(raw):
    files = [f for f in raw.get("files") or [] if isinstance(f, str)]
    n = len(files)
    r = {"n_files": n}

    lines = obj(raw.get("lines-per-file"))
    loc = [obj(lines.get(f)).get("nonEmpty", 0) or 0 for f in files]
    r["loc"] = float(sum(loc))
    r["loc_file_mean"] = nan_mean(loc)
    r["loc_file_max"] = nan_max(loc)

    r["n_functions"] = count_entries(obj(raw.get("functions-per-file")), files)
    r["n_classes"] = count_entries(obj(raw.get("classes-per-file")), files)
    cds = obj(raw.get("class-dependency-summary"))
    classes = [c for f in files for c in obj(cds.get(f)).values() if isinstance(c, dict)]
    r["n_methods"] = float(sum(c.get("methods", 0) or 0 for c in classes))

    flen = obj(raw.get("function-length"))
    lens = [x.get("lines", 0) or 0 for f in files for x in obj(flen.get(f)).values() if isinstance(x, dict)]
    r["func_length_mean"] = nan_mean(lens)
    r["func_length_median"] = float(np.median(lens)) if lens else np.nan
    r["func_length_max"] = nan_max(lens)
    pc = obj(raw.get("parameter-count"))
    params = [x.get("params", 0) or 0 for f in files for x in obj(pc.get(f)).values() if isinstance(x, dict)]
    r["params_mean"] = nan_mean(params)
    r["params_max"] = nan_max(params)

    out, inn = import_graph(obj(raw.get("file-coupling")), files)
    edges = sum(len(v) for v in out.values())
    r["file_edges"] = edges
    r["edges_per_file"] = edges / n if n else np.nan
    r["density"] = edges / (n * (n - 1)) if n >= 2 else np.nan
    coupled = [f for f in files if out[f] or inn[f]]
    r["coupled_files_pct"] = 100 * len(coupled) / n if n else np.nan
    r["max_fan_in"] = max((len(v) for v in inn.values()), default=np.nan)
    r["max_fan_out"] = max((len(v) for v in out.values()), default=np.nan)
    sizes = components(out, inn)
    r["components"] = len(sizes) if n else np.nan
    r["largest_component_pct"] = 100 * max(sizes) / n if n else np.nan
    r["cyclic_files_pct"] = 100 * cyclic_files(out) / n if n else np.nan

    ii = obj(raw.get("import-instability"))
    inst = [obj(ii.get(f)) for f in files]
    conn = [x.get("instability", 0) or 0 for x in inst
            if (x.get("afferent", 0) or 0) + (x.get("efferent", 0) or 0) > 0]
    r["instability_mean"] = nan_mean(conn)
    r["stable_pct"] = 100 * sum(1 for v in conn if v == 0) / len(conn) if conn else np.nan
    r["unstable_pct"] = 100 * sum(1 for v in conn if v == 1) / len(conn) if conn else np.nan

    dc = obj(raw.get("dependency-centrality"))
    cent = [obj(dc.get(f)).get("totalDegreeCentrality", 0) or 0 for f in files]
    r["centrality_max"] = nan_max(cent)

    fds = obj(raw.get("function-dependency-summary"))
    funcs = [x for f in files for x in obj(fds.get(f)).values() if isinstance(x, dict)]
    r["func_fan_in_mean"] = nan_mean([x.get("fanInCalls", 0) or 0 for x in funcs])
    r["func_fan_out_mean"] = nan_mean([x.get("fanOutCalls", 0) or 0 for x in funcs])
    scores = [x.get("dependencyScore", 0) or 0 for x in funcs]
    r["func_dep_score_mean"] = nan_mean(scores)
    r["func_coupled_pct"] = 100 * sum(1 for s in scores if s > 0) / len(scores) if scores else np.nan
    r["class_fan_in_mean"] = nan_mean([c.get("fanInCalls", 0) or 0 for c in classes])
    r["class_fan_out_mean"] = nan_mean([c.get("fanOutCalls", 0) or 0 for c in classes])
    r["class_dep_score_mean"] = nan_mean([c.get("dependencyScore", 0) or 0 for c in classes])

    err = obj(raw.get("errors"))
    r["parse_errors"] = len(err.get("parse") or [])
    r["traverse_errors"] = len(err.get("traverse") or [])
    return r


# Package metrics table for one sample
def build_table(folder):
    sample = pd.read_csv(str(folder / "sample.csv"))
    rows, missing = [], 0
    for i, s in enumerate(sample.itertuples(index=False), 1):
        base = {c: getattr(s, c, np.nan) for c in CONTEXT}
        try:
            with gzip.open(str(folder / "raw" / s.raw_file), "rt", encoding="utf-8") as f:
                base.update(package_row(json.load(f)))
        except Exception as e:
            missing += 1
            base["error"] = str(e)[:200]
        rows.append(base)
        if i % 500 == 0:
            print(f"    {i}/{len(sample)} packages", flush=True)
    return pd.DataFrame(rows), missing


# Mean, sd, min, quartiles and max per stratum and total
def describe(df, n_strata):
    rows = []
    groups = [(t, df[df["tramo"] == t]) for t in range(1, n_strata + 1)] + [("Total", df)]
    for m in METRICS:
        for t, g in groups:
            v = pd.to_numeric(g[m], errors="coerce").dropna()
            rows.append({"metric": m, "tramo": t, "n": len(v),
                         "mean": v.mean(), "sd": v.std(), "min": v.min(), "q1": v.quantile(0.25),
                         "median": v.median(), "q3": v.quantile(0.75), "max": v.max()})
    return pd.DataFrame(rows)


def fmt(v, d=2):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def labels_for(edges):
    return [f"{lo} o más" if i + 1 == len(edges) else f"{lo} a {edges[i + 1] - 1}"
            for i, lo in enumerate(edges)]


# Boxplots of the main metrics per stratum
def fig_boxplots(df, labels, path):
    ncol = 3
    nrow = math.ceil(len(BOXPLOT) / ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(5 * ncol, 3.6 * nrow))
    for ax, m in zip(axes.flat, BOXPLOT):
        data = [pd.to_numeric(g[m], errors="coerce").dropna().values for _, g in df.groupby("tramo")]
        if m in LOG_SCALE:
            data = [np.log10(d + 1) for d in data]
        ax.boxplot(data, showfliers=False)
        ax.set_xticks(range(1, len(labels) + 1))
        ax.set_xticklabels(labels, rotation=30, fontsize=8)
        ax.set_title(m + (" — log10(x+1)" if m in LOG_SCALE else ""), fontsize=10)
    for ax in list(axes.flat)[len(BOXPLOT):]:
        ax.axis("off")
    fig.suptitle("Métricas de JTMetrics por tramo de Fan-In (sin atípicos)")
    fig.tight_layout()
    fig.savefig(str(path), dpi=150)
    plt.close(fig)


# Write metrics_stats.md
def write_md(path, df, stats, labels, missing):
    n_strata = len(labels)
    with open(str(path), "w", encoding="utf-8") as f:
        f.write("# Métricas de JTMetrics por tramo\n\n")
        f.write(f"Generado: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"- Paquetes: {len(df):,}".replace(",", ".") + f"; sin archivo raw legible: {missing}\n")
        f.write("- Todas las métricas usan los archivos tal como los leyó JTMetrics, incluidos .d.ts y .min.js\n")
        f.write("- Grafo de importaciones: solo entre archivos analizados; las importaciones a .json, "
                ".jsx o .tsx no se cuentan\n")
        f.write("- Inestabilidad: promedio de los archivos con al menos una importación\n")
        f.write("- Métricas de funciones y clases: secundarias, por los errores de JTMetrics\n\n")
        f.write("## Contexto por tramo\n\n| Tramo | Fan-In | Paquetes | % familia | % con .d.ts | "
                "% con .min.js | Cobertura mediana |\n|---|---|---|---|---|---|---|\n")
        for t in range(1, n_strata + 1):
            g = df[df["tramo"] == t]
            f.write(f"| {t} | {labels[t - 1]} | {len(g)} | {fmt(100 * g['familia'].mean(), 1)} % | "
                    f"{fmt(100 * (g['dts_files'] > 0).mean(), 1)} % | "
                    f"{fmt(100 * (g['min_js_files'] > 0).mean(), 1)} % | "
                    f"{fmt(100 * g['coverage'].median(), 1)} % |\n")
        f.write("\n![Boxplots](figures/metrics_boxplots.png)\n\n")
        for group, ms in GROUPS.items():
            f.write(f"## {group}\n\n")
            for m in ms:
                f.write(f"### `{m}`\n\n| Tramo | n | Media | DE | Mín. | Q1 | Mediana | Q3 | Máx. |\n"
                        "|---|---|---|---|---|---|---|---|---|\n")
                for r in stats[stats["metric"] == m].itertuples():
                    name = r.tramo if r.tramo == "Total" else f"{r.tramo} ({labels[r.tramo - 1]})"
                    f.write(f"| {name} | {r.n} | {fmt(r.mean)} | {fmt(r.sd)} | {fmt(r.min)} | "
                            f"{fmt(r.q1)} | {fmt(r.median)} | {fmt(r.q3)} | {fmt(r.max)} |\n")
                f.write("\n")


# Package metrics and statistics per stratum
def main():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(str(STRATA_META), encoding="utf-8") as f:
        edges = json.load(f)["edges"][STRATA_CONFIG]
    labels = labels_for(edges)
    if not (SAMPLE / "sample.csv").exists():
        raise SystemExit(f"{SAMPLE / 'sample.csv'} not found. Run jtmetrics/sample_extract.py first.")
    print(f"Sample: {SAMPLE}", flush=True)
    df, missing = build_table(SAMPLE)
    df.to_csv(str(SAMPLE / "package_metrics.csv"), index=False, encoding="utf-8")
    stats = describe(df, len(edges))
    stats.to_csv(str(SAMPLE / "metrics_stats.csv"), index=False, encoding="utf-8")
    (SAMPLE / "figures").mkdir(exist_ok=True)
    fig_boxplots(df, labels, SAMPLE / "figures" / "metrics_boxplots.png")
    write_md(SAMPLE / "metrics_stats.md", df, stats, labels, missing)
    with open(str(SAMPLE / "package_metrics_run.json"), "w", encoding="utf-8") as f:
        json.dump({"executed_at": started, "packages": int(len(df)), "missing_raw": missing,
                   "metrics": METRICS}, f, indent=2)
    print(f"Done. {len(df)} packages, {missing} without readable raw. Results in {SAMPLE}")


if __name__ == "__main__":
    main()
