import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
# Import config.py from the root
sys.path.insert(0, str(BASE))
from config import USER_AGENT

INPUT = BASE / "data" / "fanin_population" / "fanin_population.parquet"
STRATA_META = BASE / "data" / "strata_definition" / "run_metadata.json"
STRATA_CONFIG = "6 tramos, con pico"
RUNNER = HERE / "jtmetrics_runner.mjs"
DIR_OUT = BASE / "data" / "strata_jtmetrics_sample"
DIR_TMP = DIR_OUT / "tmp"
DIR_RAW = DIR_OUT / "raw"
ATTEMPTS = DIR_OUT / "attempts.csv"

K = 2
P = 0.5
E = 0.05
COVERAGE_MIN = 0.25
SEED = 2028
WORKERS = 4
BATCH_MARGIN = 1.15
DOWNLOAD_TIMEOUT_S = 120
DOWNLOAD_TRIES = 2
JTMETRICS_TIMEOUT_S = 600
LOG_EVERY = 100
NODE_MAX_MB = 8192
RETRY_STATUSES = ("jtmetrics_error",)

SUPPORTED_CODE = (".js", ".cjs", ".ts")
UNSUPPORTED_CODE = (".mjs", ".mts", ".cts", ".jsx", ".tsx")
DTS_SUFFIXES = (".d.ts", ".d.cts", ".d.mts")
MIN_SUFFIXES = (".min.js",)
VENDOR_DIR = "node_modules"

COLS = ["name", "scope", "scope_size", "dep_hash", "fan_in", "tarball"]
FIELDS = [
    "tramo", "order", "name", "fan_in", "familia", "status", "valid",
    "coverage", "lines_supported", "lines_unsupported",
    "lines_dts", "lines_min_js",
    "files_in_tarball", "files_skipped", "code_files_supported", "code_files_unsupported",
    "dts_files", "min_js_files", "node_modules_files",
    "t_download_s", "t_extract_s", "t_jtmetrics_s", "t_total_s",
    "tarball_bytes", "raw_file",
    "n_files", "lines_non_empty", "n_functions", "n_classes",
    "internal_edges", "coupled_files", "mean_instability",
    "parse_errors", "file_errors", "traverse_errors", "metric_errors",
    "error",
]


# Strata cuts from 09
def load_edges():
    with open(str(STRATA_META), encoding="utf-8") as f:
        return json.load(f)["edges"][STRATA_CONFIG]


# Finite population sample size per stratum
def stratum_size(n_pop):
    if n_pop <= 1:
        return int(n_pop)
    q = 1 - P
    return math.ceil(K ** 2 * P * q * n_pop / ((n_pop - 1) * E ** 2 + K ** 2 * P * q))


# Resulting error for n packages in a stratum of n_pop
def stratum_error(n, n_pop):
    if n == 0 or n_pop <= 1:
        return float("nan")
    return K * math.sqrt(P * (1 - P) / n * (n_pop - n) / (n_pop - 1))


# Random order per stratum, one per scope and non-empty dep_hash
def candidate_lists(df, edges):
    rng = np.random.default_rng(SEED)
    df = df.copy()
    df["tramo"] = np.searchsorted(np.array(edges), df["fan_in"].values, side="right")
    df["familia"] = (df["scope_size"] >= 2).astype(int)
    lists = {}
    for t in range(1, len(edges) + 1):
        sub = df[df["tramo"] == t]
        sub = sub.iloc[rng.permutation(len(sub))]
        scope = sub["scope"].fillna("").astype(str)
        sub = sub[~((scope != "") & scope.duplicated()).values]
        dh = sub["dep_hash"].fillna("").astype(str)
        sub = sub[~((dh != "") & dh.duplicated()).values]
        sub = sub.reset_index(drop=True)
        sub["order"] = np.arange(1, len(sub) + 1)
        lists[t] = sub
    return lists


# Download tarball
def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(DOWNLOAD_TRIES):
        try:
            with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT_S) as r, \
                    open(str(dest), "wb") as f:
                shutil.copyfileobj(r, f)
            return
        except Exception:
            if attempt == DOWNLOAD_TRIES - 1:
                raise
            time.sleep(3)


# Extract regular files only, skip unsafe paths
def safe_extract(tgz, dest):
    written = skipped = 0
    dest = dest.resolve()
    with tarfile.open(str(tgz), "r:*") as tar:
        for m in tar:
            if not m.isfile():
                continue
            parts = [p for p in m.name.replace("\\", "/").split("/") if p not in ("", ".")]
            if not parts or ".." in parts:
                skipped += 1
                continue
            target = dest.joinpath(*parts)
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(str(target), "wb") as f:
                    shutil.copyfileobj(tar.extractfile(m), f)
                written += 1
            except (OSError, tarfile.TarError):
                skipped += 1
    return written, skipped


def count_lines(path):
    try:
        with open(path, "rb") as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return 0


# Files and non-empty lines by type; .d.ts and .min.js are left out of coverage
def classify(root):
    c = dict.fromkeys(["supported", "unsupported", "dts", "min_js", "node_modules",
                       "l_supported", "l_unsupported", "l_dts", "l_min_js"], 0)
    for dirpath, _, filenames in os.walk(str(root)):
        in_vendor = VENDOR_DIR in Path(dirpath).parts
        for fn in filenames:
            low = fn.lower()
            full = os.path.join(dirpath, fn)
            if low.endswith(DTS_SUFFIXES):
                c["dts"] += 1
                c["l_dts"] += count_lines(full)
                if low.endswith(SUPPORTED_CODE):
                    c["supported"] += 1
            elif low.endswith(MIN_SUFFIXES):
                c["min_js"] += 1
                c["supported"] += 1
                c["l_min_js"] += count_lines(full)
            elif low.endswith(SUPPORTED_CODE):
                c["supported"] += 1
                c["l_supported"] += count_lines(full)
                if in_vendor:
                    c["node_modules"] += 1
            elif low.endswith(UNSUPPORTED_CODE):
                c["unsupported"] += 1
                c["l_unsupported"] += count_lines(full)
    return c


def raw_name(name):
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in name)
    return f"{safe[:80]}_{hashlib.md5(name.encode()).hexdigest()[:8]}.json.gz"


# Download, extract, check coverage and measure one package
def process(row):
    rec = {k: "" for k in FIELDS}
    rec.update(tramo=int(row.tramo), order=int(row.order), name=row.name,
               fan_in=int(row.fan_in), familia=int(row.familia), valid=0)
    work = DIR_TMP / f"t{row.tramo}_{row.order}"
    t0 = time.perf_counter()
    try:
        shutil.rmtree(str(work), ignore_errors=True)
        work.mkdir(parents=True)
        tgz, code = work / "pkg.tgz", work / "code"
        if not isinstance(row.tarball, str) or not row.tarball:
            rec["status"] = "no_tarball_url"
            return rec
        try:
            download(row.tarball, tgz)
        except Exception as e:
            rec.update(status="download_error", error=str(e)[:200])
            return rec
        t1 = time.perf_counter()
        rec["t_download_s"] = round(t1 - t0, 3)
        rec["tarball_bytes"] = tgz.stat().st_size
        try:
            rec["files_in_tarball"], rec["files_skipped"] = safe_extract(tgz, code)
        except Exception as e:
            rec.update(status="extract_error", error=str(e)[:200])
            return rec
        t2 = time.perf_counter()
        rec["t_extract_s"] = round(t2 - t1, 3)
        c = classify(code)
        rec.update(code_files_supported=c["supported"], code_files_unsupported=c["unsupported"],
                   dts_files=c["dts"], min_js_files=c["min_js"],
                   node_modules_files=c["node_modules"],
                   lines_supported=c["l_supported"], lines_unsupported=c["l_unsupported"],
                   lines_dts=c["l_dts"], lines_min_js=c["l_min_js"])
        total = c["l_supported"] + c["l_unsupported"]
        if total == 0:
            rec["status"] = "no_code"
            return rec
        cov = c["l_supported"] / total
        rec["coverage"] = round(cov, 4)
        if cov < COVERAGE_MIN:
            rec["status"] = "low_coverage"
            return rec
        raw_file = raw_name(row.name)
        # Run JTMetrics through Node
        cmd = ["node", f"--max-old-space-size={NODE_MAX_MB}", str(RUNNER),
               str(code.resolve()), "-", str(DIR_RAW / raw_file)]
        try:
            p = subprocess.run(cmd, cwd=str(HERE), capture_output=True, text=True,
                               timeout=JTMETRICS_TIMEOUT_S, encoding="utf-8",
                               errors="replace")
        except subprocess.TimeoutExpired:
            rec.update(status="timeout", t_jtmetrics_s=JTMETRICS_TIMEOUT_S)
            return rec
        rec["t_jtmetrics_s"] = round(time.perf_counter() - t2, 3)
        if p.returncode != 0:
            rec.update(status="jtmetrics_error", error=(p.stderr or p.stdout).strip()[-200:])
            return rec
        rec.update(json.loads(p.stdout.strip().splitlines()[-1]))
        rec["raw_file"] = raw_file
        rec["status"] = "ok"
        rec["valid"] = 1
        return rec
    except Exception as e:
        rec.update(status="script_error", error=str(e)[:200])
        return rec
    finally:
        rec["t_total_s"] = round(time.perf_counter() - t0, 3)
        shutil.rmtree(str(work), ignore_errors=True)


def load_attempts():
    if not ATTEMPTS.exists():
        return pd.DataFrame(columns=FIELDS)
    return pd.read_csv(str(ATTEMPTS))


# Measure candidates in order until a stratum reaches its target
def run_stratum(t, cands, target, done, writer, fh, pool):
    tried = done[done["tramo"] == t]
    tried_names = set(tried["name"])
    valid = int(tried["valid"].sum())
    pos = 0
    n_new = 0
    t_start = time.perf_counter()
    # Fill gaps first: untried candidates before the last order tried
    max_order = int(tried["order"].max()) if len(tried) else 0
    gaps = cands[(cands["order"] <= max_order) & (~cands["name"].isin(tried_names))]
    if len(gaps):
        print(f"  tramo {t}: retrying {len(gaps)} packages", flush=True)
        for rec in pool.map(process, gaps.itertuples(index=False)):
            writer.writerow(rec)
            fh.flush()
            tried_names.add(rec["name"])
            valid += rec["valid"]
            n_new += 1
            print(f"    {rec['name']}: {rec['status']}", flush=True)
    while valid < target:
        rate = valid / len(tried_names) if len(tried_names) >= 30 else 0.9
        need = target - valid
        batch_size = max(WORKERS, math.ceil(need / max(rate, 0.05) * BATCH_MARGIN))
        batch = []
        while pos < len(cands) and len(batch) < batch_size:
            r = cands.iloc[pos]
            pos += 1
            if r["name"] not in tried_names:
                batch.append(r)
        if not batch:
            print(f"  tramo {t}: candidate list exhausted with {valid} valid")
            break
        print(f"  tramo {t}: measuring {len(batch)} packages "
              f"({valid} of {target} valid so far)", flush=True)
        rows = pd.DataFrame(batch).itertuples(index=False)
        for rec in pool.map(process, rows):
            writer.writerow(rec)
            fh.flush()
            tried_names.add(rec["name"])
            valid += rec["valid"]
            n_new += 1
            # Progress every LOG_EVERY packages
            if n_new % LOG_EVERY == 0:
                el = time.perf_counter() - t_start
                print(f"  tramo {t}: {len(tried_names)} tried, {valid} valid, "
                      f"{n_new / el * 3600:,.0f} packages/h", flush=True)
        print(f"  tramo {t}: {valid} valid of {len(tried_names)} tried", flush=True)


# Final sample: first n_h valid packages by candidate order
def mark_sample(att, targets):
    att = att.sort_values(["tramo", "order"]).copy()
    att["valid_rank"] = att.groupby("tramo")["valid"].cumsum().where(att["valid"] == 1)
    att["in_sample"] = ((att["valid"] == 1)
                        & (att["valid_rank"] <= att["tramo"].map(targets))).astype(int)
    return att


def fmt(v, d=0):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# Write results.md
def write_results(att, edges, wall_s, alloc):
    labels = [f"{lo} o más" if i + 1 == len(edges) else f"{lo} a {edges[i + 1] - 1}"
              for i, lo in enumerate(edges)]
    statuses = ["ok", "low_coverage", "no_code", "download_error", "extract_error",
                "jtmetrics_error", "timeout", "no_tarball_url", "script_error"]
    with open(str(DIR_OUT / "results.md"), "w", encoding="utf-8") as f:
        f.write("# Extracción con JTMetrics: tamaño de muestra por tramo\n\n")
        f.write(f"Generado: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Configuración\n\n")
        f.write(f"- Tramos: {STRATA_CONFIG} (límites {', '.join(map(str, edges))})\n")
        f.write("- Meta por tramo: nₕ = K² · p · q · Nₕ / ((Nₕ − 1) · e² + K² · p · q), "
                "redondeado hacia arriba\n")
        f.write(f"- Parámetros: K = {K}, p = {P}, q = {1 - P}, e = {E}\n")
        f.write(f"- Semilla {SEED}; máximo uno por scope y uno por `dep_hash` no vacío\n")
        f.write(f"- Válido: JTMetrics terminó y la cobertura es al menos "
                f"{int(COVERAGE_MIN * 100)} %\n")
        f.write("- Cobertura: líneas no vacías en .js, .cjs y .ts sobre ese total más "
                ".mjs, .mts, .cts, .jsx y .tsx; sin .d.ts ni .min.js\n")
        f.write("- JTMetrics se ejecuta sin excluir archivos; .d.ts y .min.js se "
                "excluyen después, al calcular las métricas por paquete\n")
        f.write(f"- Tiempo de la última ejecución: {fmt(wall_s / 60, 1)} min\n\n")

        f.write("## Tamaño de muestra por tramo\n\n| Tramo | Fan-In | Nₕ | nₕ | eₕ |\n"
                "|---|---|---|---|---|\n")
        for r in alloc.itertuples():
            f.write(f"| {r.tramo} | {labels[r.tramo - 1]} | {fmt(r.N_h)} | {fmt(r.n_h)} | "
                    f"{fmt(100 * r.e_h, 2)} % |\n")
        f.write(f"| Total | | {fmt(alloc['N_h'].sum())} | {fmt(alloc['n_h'].sum())} | |\n\n")

        f.write("## Intentos por tramo\n\n| Tramo | Fan-In | Intentados | Válidos | "
                "En la muestra | " + " | ".join(statuses[1:]) + " |\n")
        f.write("|---|---|---|---|---|" + "---|" * (len(statuses) - 1) + "\n")
        for t in range(1, len(edges) + 1):
            a = att[att["tramo"] == t]
            vc = a["status"].value_counts()
            f.write(f"| {t} | {labels[t - 1]} | {fmt(len(a))} | {fmt(int(a['valid'].sum()))} | "
                    f"{fmt(int(a['in_sample'].sum()))} | "
                    + " | ".join(fmt(int(vc.get(s, 0))) for s in statuses[1:]) + " |\n")
        f.write("\n## Cobertura por tramo\n\n")
        f.write("Paquetes con código analizable (cobertura calculada).\n\n")
        f.write("| Tramo | Paquetes | Mediana | % con 100 % | % entre 25 % y 99 % | "
                "% bajo 25 % |\n|---|---|---|---|---|---|\n")
        for t in range(1, len(edges) + 1):
            cv = pd.to_numeric(att.loc[att["tramo"] == t, "coverage"], errors="coerce").dropna()
            n = len(cv)
            f.write(f"| {t} | {fmt(n)} | {fmt(100 * cv.median(), 1) if n else '—'} % | "
                    f"{fmt(100 * (cv >= 1).mean(), 1) if n else '—'} % | "
                    f"{fmt(100 * ((cv >= COVERAGE_MIN) & (cv < 1)).mean(), 1) if n else '—'} % | "
                    f"{fmt(100 * (cv < COVERAGE_MIN).mean(), 1) if n else '—'} % |\n")
        f.write("\n## Muestra final\n\n")
        s = att[att["in_sample"] == 1]
        f.write("| Tramo | Paquetes | % familia | Mediana Fan-In | Mediana de archivos | "
                "% con .d.ts | % con .min.js |\n|---|---|---|---|---|---|---|\n")
        for t in range(1, len(edges) + 1):
            g = s[s["tramo"] == t]
            n = len(g)
            f.write(f"| {t} | {fmt(n)} | {fmt(100 * g['familia'].mean(), 1) if n else '—'} % | "
                    f"{fmt(g['fan_in'].median()) if n else '—'} | "
                    f"{fmt(pd.to_numeric(g['n_files']).median()) if n else '—'} | "
                    f"{fmt(100 * (pd.to_numeric(g['dts_files']) > 0).mean(), 1) if n else '—'} % | "
                    f"{fmt(100 * (pd.to_numeric(g['min_js_files']) > 0).mean(), 1) if n else '—'} % |\n")
        f.write("\nLas columnas de JTMetrics en `attempts.csv` (n_files, internal_edges y "
                "otras) incluyen todos los archivos leídos. Las métricas por paquete, sin "
                ".d.ts ni .min.js, se calculan después desde `raw/`.\n")


# Check Node and jtmetrics
def check_node():
    try:
        p = subprocess.run(["node", "-e", "import('jtmetrics').then(()=>console.log('ok'))"],
                           cwd=str(HERE), capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        raise SystemExit("Node.js not found. Install Node >= 18.")
    if "ok" not in p.stdout:
        raise SystemExit("jtmetrics not installed. Run `npm ci --ignore-scripts` "
                         "inside jtmetrics/.\n" + p.stderr)


# Extraction
def main():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    check_node()
    edges = load_edges()
    print(f"Strata ({STRATA_CONFIG}): {edges}")
    df = pd.read_parquet(str(INPUT), columns=COLS)
    df = df[df["fan_in"] > 0].reset_index(drop=True)
    lists = candidate_lists(df, edges)
    for d in (DIR_OUT, DIR_TMP, DIR_RAW):
        d.mkdir(parents=True, exist_ok=True)

    # Target per stratum from its population size
    tramo = np.searchsorted(np.array(edges), df["fan_in"].values, side="right")
    pop = pd.Series(tramo).value_counts().reindex(range(1, len(edges) + 1), fill_value=0)
    alloc = pd.DataFrame({"tramo": pop.index.astype(int), "N_h": pop.values.astype(int)})
    alloc["n_h"] = alloc["N_h"].apply(stratum_size)
    alloc["e_h"] = [stratum_error(n, N) for n, N in zip(alloc["n_h"], alloc["N_h"])]
    alloc.to_csv(str(DIR_OUT / "allocation.csv"), index=False, encoding="utf-8")
    targets = dict(zip(alloc["tramo"], alloc["n_h"]))
    print("Targets per stratum: " + ", ".join(f"{t}: {n}" for t, n in targets.items()))

    done = load_attempts()
    # Drop failed attempts so they are measured again
    retry = done["status"].isin(RETRY_STATUSES)
    if retry.any():
        done = done[~retry]
        done.to_csv(str(ATTEMPTS), index=False, encoding="utf-8")
        print(f"Retrying {int(retry.sum())} packages with status {', '.join(RETRY_STATUSES)}")
    new_file = not ATTEMPTS.exists()
    t0 = time.perf_counter()
    with open(str(ATTEMPTS), "a", newline="", encoding="utf-8") as fh, \
            ThreadPoolExecutor(max_workers=WORKERS) as pool:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        if new_file:
            w.writeheader()
        for t in range(1, len(edges) + 1):
            print(f"Tramo {t}: {len(lists[t]):,} candidates", flush=True)
            run_stratum(t, lists[t], targets[t], done, w, fh, pool)
    wall_s = time.perf_counter() - t0
    shutil.rmtree(str(DIR_TMP), ignore_errors=True)

    att = mark_sample(load_attempts(), targets)
    att.to_csv(str(DIR_OUT / "attempts_marked.csv"), index=False, encoding="utf-8")
    att[att["in_sample"] == 1].drop(columns=["valid_rank"]).to_csv(
        str(DIR_OUT / "sample.csv"), index=False, encoding="utf-8")
    write_results(att, edges, wall_s, alloc)
    with open(str(DIR_OUT / "run_metadata.json"), "w", encoding="utf-8") as f:
        json.dump({"executed_at": started, "strata_config": STRATA_CONFIG, "edges": edges,
                   "allocation": "finite population formula per stratum",
                   "K": K, "p": P, "e": E, "targets": {str(k): int(v) for k, v in targets.items()},
                   "coverage_min": COVERAGE_MIN,
                   "seed": SEED, "workers": WORKERS, "jtmetrics_version": "1.1.0",
                   "node_max_old_space_mb": NODE_MAX_MB,
                   "wall_seconds": wall_s, "attempts": int(len(att)),
                   "in_sample": int(att["in_sample"].sum())},
                  f, indent=2, ensure_ascii=False)
    print(f"Done in {wall_s / 60:.1f} min. Results in {DIR_OUT}")


if __name__ == "__main__":
    main()
