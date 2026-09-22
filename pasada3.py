#!/usr/bin/env python3
"""
Pasada 3 -- Grafo de dependencias y metricas externas.

Cubre pasos 4 (aristas), 5 (normalizar), 6 (colgantes) y 10 (Fan-In/Out).
Entrada: data/pasada2/*.jsonl.

Salidas:
  data/metricas_externas.csv   tabla final por paquete
  data/colgantes.txt           destinos inexistentes, por frecuencia
  data/resumen_grafo.json      estadisticas del grafo
"""
import json, glob, time, os
from collections import Counter
from config import SNAPSHOT_SEQ

IN_DIR   = "data/pasada2"
OUT_CSV  = "data/metricas_externas.csv"
OUT_COLG = "data/colgantes.txt"
OUT_RES  = "data/resumen_grafo.json"


def norm(nombre):
    """Paso 5. Respeta @scope/nombre; npm es case-insensitive."""
    return nombre.strip().lower()


def main():
    t0 = time.time()

    # ---- 1. Cargar nodos y dependencias ------
    print("Leyendo shards...")
    nodos       = set()
    deps_de     = {}
    devdeps_de  = {}
    sin_version = set()
    n_404 = lineas = 0

    for f in sorted(glob.glob(f"{IN_DIR}/*.jsonl")):
        for line in open(f, encoding="utf-8"):
            d = json.loads(line)
            lineas += 1

            nombre = norm(d["name"])

            if "error" in d:
                n_404 += 1
                nodos.add(nombre)           # nodo fantasma: recibe Fan-In, sin Fan-Out
                continue
            nodos.add(nombre)

            if d.get("sin_version"):
                sin_version.add(nombre)
                continue                    # nodo valido, sin Fan-Out

            deps_de[nombre]    = [norm(x) for x in d.get("deps", [])]
            devdeps_de[nombre] = [norm(x) for x in d.get("dev_deps", [])]

    print(f"  lineas        : {lineas:,}")
    print(f"  nodos reales  : {len(nodos):,}")
    print(f"  con version   : {len(deps_de):,}")
    print(f"  sin version   : {len(sin_version):,}")
    print(f"  descartados   : {n_404:,} (404)")

    # ---- 2. Aristas y colgantes (pasos 4 y 6) ------------------------
    print("\nConstruyendo aristas...")
    fan_out = Counter(); fan_in = Counter()
    fo_dev  = Counter(); fi_dev = Counter()
    colg    = Counter(); colg_dev = Counter()
    ar = ar_dev = 0

    for origen, dsts in deps_de.items():
        fan_out[origen] = len(dsts)
        ar += len(dsts)
        for dst in dsts:
            if dst in nodos:
                fan_in[dst] += 1
            else:
                colg[dst] += 1

    for origen, dsts in devdeps_de.items():
        fo_dev[origen] = len(dsts)
        ar_dev += len(dsts)
        for dst in dsts:
            if dst in nodos:
                fi_dev[dst] += 1
            else:
                colg_dev[dst] += 1

    print(f"  aristas deps    : {ar:,}")
    print(f"  aristas devDeps : {ar_dev:,}")
    print(f"  colgantes deps  : {len(colg):,} distintos / "
          f"{sum(colg.values()):,} refs")

    # ---- 3. Tabla final (paso 10) ------------------------------------
    print("\nEscribiendo salidas...")
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        f.write("paquete,fan_in,fan_out,fan_in_dev,fan_out_dev,sin_version\n")
        for n in sorted(nodos):
            nom = f'"{n}"' if ("," in n or '"' in n) else n
            f.write(f"{nom},{fan_in.get(n,0)},{fan_out.get(n,0)},"
                    f"{fi_dev.get(n,0)},{fo_dev.get(n,0)},"
                    f"{1 if n in sin_version else 0}\n")

    with open(OUT_COLG, "w", encoding="utf-8") as f:
        f.write("# destino\trefs_deps\trefs_devdeps\n")
        for c in sorted(set(colg) | set(colg_dev),
                        key=lambda x: -(colg[x] + colg_dev[x])):
            f.write(f"{c}\t{colg[c]}\t{colg_dev[c]}\n")

    # ---- 4. Estadisticas --------------------------------------------
    fi_todos = [fan_in.get(n, 0) for n in nodos]
    cero     = sum(1 for x in fi_todos if x == 0)
    seis     = sum(1 for x in fi_todos if x >= 6)
    con_dep  = sum(1 for n in deps_de if fan_out[n] > 0)

    res = {
        "fecha":              time.strftime("%Y-%m-%d %H:%M"),
        "snapshot_seq":       SNAPSHOT_SEQ,
        "nodos":              len(nodos),
        "con_version":        len(deps_de),
        "sin_version":        len(sin_version),
        "descartados_404":    n_404,
        "aristas_deps":       ar,
        "aristas_devdeps":    ar_dev,
        "colgantes_distintos": len(colg),
        "colgantes_refs":     sum(colg.values()),
        "fan_in_cero_pct":    round(cero / len(nodos) * 100, 2),
        "fan_in_6mas_pct":    round(seis / len(nodos) * 100, 2),
        "con_1dep_pct":       round(con_dep / len(deps_de) * 100, 2),
    }
    json.dump(res, open(OUT_RES, "w"), indent=2)

    # ---- 5. Reporte -------------------------------------------------
    print(f"\n{'='*60}")
    print(f"  Nodos              : {len(nodos):>12,}")
    print(f"  Aristas (deps)     : {ar:>12,}")
    print(f"  Aristas (devDeps)  : {ar_dev:>12,}")
    print(f"{'-'*60}")
    print(f"  VALIDACION vs Wittern et al. (2016)")
    print(f"    Fan-In = 0   : {res['fan_in_cero_pct']:>6}%   (ellos 72.5%)")
    print(f"    Fan-In >= 6  : {res['fan_in_6mas_pct']:>6}%   (ellos  4.9%)")
    print(f"    Con >=1 dep  : {res['con_1dep_pct']:>6}%   (ellos 81.3%)")
    print(f"{'-'*60}")
    print(f"  Tiempo             : {(time.time()-t0)/60:>12.1f} min")
    print(f"{'='*60}")

    print("\nTop 15 por Fan-In:")
    for n, v in fan_in.most_common(15):
        print(f"  {v:>9,}  {n}")


if __name__ == "__main__":
    main()