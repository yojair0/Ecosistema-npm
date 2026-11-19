import json
import time
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
INPUT = BASE / "data" / "fanin_population" / "fanin_population.parquet"
DIR_OUT = BASE / "data" / "strata_definition"

COLS = ["name", "scope", "scope_size", "dep_hash", "fan_in"]
N_STRATA = [6, 7]
PEAK_VALUE = 9
FINE_MAX = 1000
FAMILY_MIN_SIZE = 2
SEED = 42


# Fine classes: 1..1000, then doubling
def fine_classes(max_val):
    lo = list(range(1, min(max_val, FINE_MAX) + 1))
    if max_val > FINE_MAX:
        lo.append(FINE_MAX + 1)
        e = 2 * FINE_MAX
        while e <= max_val:
            lo.append(e)
            e *= 2
    return np.array(lo, dtype=np.int64)


# Packages per class
def class_frequencies(values, class_lo):
    idx = np.searchsorted(class_lo, values, side="right") - 1
    return np.bincount(idx, minlength=len(class_lo)).astype(np.float64)


# Replace f(9) by sqrt(f(8) * f(10))
def remove_peak(freq, class_lo, value):
    f = freq.copy()
    pos = {int(v): i for i, v in enumerate(class_lo[:FINE_MAX])}
    i, left, right = pos[value], pos[value - 1], pos[value + 1]
    expected = float(np.sqrt(f[left] * f[right]))
    observed = float(f[i])
    f[i] = min(observed, expected)
    return f, observed, expected


# Dalenius-Hodges cuts
def dalenius_hodges_edges(freq, class_lo, n_strata):
    cum = np.cumsum(np.sqrt(freq))
    total = cum[-1]
    edges = [int(class_lo[0])]
    for k in range(1, n_strata):
        idx = int(np.argmin(np.abs(cum - total * k / n_strata)))
        if idx + 1 < len(class_lo):
            edge = int(class_lo[idx + 1])
            if edge not in edges:
                edges.append(edge)
    return sorted(edges)


# Stratum labels
def labels_for(edges, max_val):
    out = []
    for i, lo in enumerate(edges):
        hi = edges[i + 1] - 1 if i + 1 < len(edges) else None
        if hi is None:
            out.append(f"{lo:,} o más".replace(",", "."))
        elif hi == lo:
            out.append(f"{lo:,}".replace(",", "."))
        else:
            out.append(f"{lo:,} a {hi:,}".replace(",", "."))
    return out


# Stratum of each package
def assign(values, edges):
    return np.searchsorted(np.array(edges), values, side="right") - 1


# Packages left after scope and dep_hash limits
def available_after_limits(sub, rng):
    if len(sub) == 0:
        return 0
    order = rng.permutation(len(sub))
    s = sub.iloc[order]
    scope = s["scope"].fillna("").astype(str)
    has_scope = scope != ""
    keep = ~(has_scope & scope.duplicated())
    s = s[keep.values]
    dh = s["dep_hash"].fillna("").astype(str)
    keep = ~((dh != "") & dh.duplicated())
    return int(keep.sum())


# Table per stratum
def strata_table(df, edges, rng):
    fi = df["fan_in"].values
    st = assign(fi, edges)
    labels = labels_for(edges, int(fi.max()))
    rows = []
    n_total = len(df)
    for k, lab in enumerate(labels):
        mask = st == k
        sub = df[mask]
        n = int(mask.sum())
        rows.append({
            "tramo": k + 1,
            "fan_in": lab,
            "desde": edges[k],
            "hasta": edges[k + 1] - 1 if k + 1 < len(edges) else int(fi.max()),
            "n": n,
            "pct_poblacion": 100 * n / n_total if n_total else 0.0,
            "mediana_fan_in": float(np.median(sub["fan_in"])) if n else np.nan,
            "pct_familia": 100 * float((sub["scope_size"] >= FAMILY_MIN_SIZE).mean()) if n else np.nan,
            "n_fan_in_9": int((sub["fan_in"] == PEAK_VALUE).sum()),
            "disponibles_tras_limites": available_after_limits(sub, rng),
        })
    return pd.DataFrame(rows)


# Number formatting
def fmt(n):
    return f"{n:,}".replace(",", ".")


def fmtp(v):
    return f"{v:.1f}".replace(".", ",") + " %"


# Markdown table
def md_table(t):
    head = ("| Tramo | Fan-In | Paquetes | % población | Mediana Fan-In | "
            "% familia | Con Fan-In 9 | Disponibles tras límites |")
    sep = "|---|---|---|---|---|---|---|---|"
    lines = [head, sep]
    for r in t.itertuples():
        lines.append(
            f"| {r.tramo} | {r.fan_in} | {fmt(r.n)} | {fmtp(r.pct_poblacion)} | "
            f"{fmt(int(r.mediana_fan_in))} | {fmtp(r.pct_familia)} | "
            f"{fmt(r.n_fan_in_9)} | {fmt(r.disponibles_tras_limites)} |")
    return "\n".join(lines)


# Write results.md
def write_results(path, df, configs, peak_info):
    n = len(df)
    with open(str(path), "w", encoding="utf-8") as f:
        f.write("# Tramos de Fan-In por Dalenius-Hodges\n\n")
        f.write(f"Generado: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Entradas\n\n")
        f.write(f"- Población: `{INPUT.relative_to(BASE)}` (G1, Fan-In > 0)\n")
        f.write(f"- Paquetes: {fmt(n)}\n")
        f.write(f"- Fan-In: del registro, sin modificar (máximo {fmt(int(df['fan_in'].max()))})\n\n")
        f.write("## Método\n\n")
        f.write("- Regla de Dalenius-Hodges: cortes en partes iguales de la suma "
                "acumulada de √f.\n")
        f.write(f"- Clases finas: cada entero de 1 a {fmt(FINE_MAX)}; sobre "
                f"{fmt(FINE_MAX)}, intervalos que duplican el ancho.\n")
        f.write(f"- Sin pico: la frecuencia de Fan-In {PEAK_VALUE} se reemplaza por "
                f"√(f({PEAK_VALUE - 1}) · f({PEAK_VALUE + 1})). Observada: "
                f"{fmt(int(peak_info['observed']))}; esperada: "
                f"{fmt(int(round(peak_info['expected'])))}; exceso: "
                f"{fmt(int(round(peak_info['observed'] - peak_info['expected'])))}.\n")
        f.write("- Los paquetes no cambian: el pico solo se corrige para calcular "
                "los cortes; los conteos por tramo usan la población completa.\n")
        f.write("- Disponibles tras límites: paquetes que quedan en el tramo al "
                "dejar como máximo uno por scope y uno por `dep_hash` no vacío "
                f"(orden aleatorio, semilla {SEED}). Es una cota aproximada de lo "
                "que se puede sortear.\n")
        f.write(f"- Familia: `scope_size >= {FAMILY_MIN_SIZE}`.\n\n")

        f.write("## Cortes por configuración\n\n")
        f.write("| Configuración | Tramos | Límites inferiores |\n|---|---|---|\n")
        for c in configs:
            f.write(f"| {c['name']} | {len(c['edges'])} | "
                    f"{', '.join(fmt(e) for e in c['edges'])} |\n")
        f.write("\n")

        f.write("## ¿El pico mueve los cortes?\n\n")
        for k in N_STRATA:
            a = next(c for c in configs if c["k"] == k and c["peak"])
            b = next(c for c in configs if c["k"] == k and not c["peak"])
            same = a["edges"] == b["edges"]
            f.write(f"- {k} tramos: "
                    + ("los cortes son iguales con y sin pico.\n" if same else
                       f"los cortes cambian ({', '.join(fmt(e) for e in a['edges'])} "
                       f"con pico; {', '.join(fmt(e) for e in b['edges'])} sin pico).\n"))
        f.write("\n")

        for c in configs:
            f.write(f"## {c['name']}\n\n")
            f.write(md_table(c["table"]) + "\n\n")


# Strata calculation
def main():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Loading {INPUT} ...")
    df = pd.read_parquet(str(INPUT), columns=COLS)
    df = df[df["fan_in"] > 0].reset_index(drop=True)
    fi = df["fan_in"].values.astype(np.int64)
    print(f"  packages: {len(df):,}  max fan_in: {fi.max():,}")

    class_lo = fine_classes(int(fi.max()))
    freq = class_frequencies(fi, class_lo)
    freq_np, observed, expected = remove_peak(freq, class_lo, PEAK_VALUE)
    print(f"  fan_in = {PEAK_VALUE}: observed {observed:,.0f}, expected {expected:,.0f}")

    configs = []
    for k in N_STRATA:
        for peak in (True, False):
            rng = np.random.default_rng(SEED)
            edges = dalenius_hodges_edges(freq if peak else freq_np, class_lo, k)
            name = f"{k} tramos, {'con' if peak else 'sin'} pico"
            table = strata_table(df, edges, rng)
            table.insert(0, "configuracion", name)
            configs.append({"name": name, "k": k, "peak": peak,
                            "edges": edges, "table": table})
            print(f"  {name}: edges {edges}")
            if len(edges) < k:
                print(f"    WARNING: only {len(edges)} distinct strata")

    DIR_OUT.mkdir(parents=True, exist_ok=True)
    pd.concat([c["table"] for c in configs]).to_csv(
        DIR_OUT / "strata.csv", index=False, encoding="utf-8")
    write_results(DIR_OUT / "results.md", df, configs,
                  {"observed": observed, "expected": expected})
    meta = {
        "executed_at": started,
        "input": str(INPUT),
        "n_packages": int(len(df)),
        "n_strata": N_STRATA,
        "fine_classes": f"1..{FINE_MAX}, then doubling",
        "peak": {"value": PEAK_VALUE, "observed": observed, "expected": expected,
                 "rule": "sqrt(f(v-1) * f(v+1))"},
        "sampling_limits": "max 1 per scope, max 1 per non-empty dep_hash, per stratum",
        "family": f"scope_size >= {FAMILY_MIN_SIZE}",
        "seed": SEED,
        "edges": {c["name"]: c["edges"] for c in configs},
    }
    with open(str(DIR_OUT / "run_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"Done. Results in {DIR_OUT}")


if __name__ == "__main__":
    main()
