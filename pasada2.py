#!/usr/bin/env python3
"""
Pasada 2 -- Contenido de cada paquete del registro npm.

Lee los nombres vivos de la Pasada 1 y consulta la API del registro
para extraer dependencias, devDependencies y tarball.

Formato abreviado (Accept: application/vnd.npm.install-v1+json).
Ese formato NO incluye 'repository' -- verificado 18-09-2026.

Entrada : data/pasada1/*.jsonl
Salida  : data/pasada2/shard_NNNNN.jsonl
Estado  : data/checkpoint2.json  (reanudable con Ctrl+C)
"""
import json, os, time, glob, signal, sys
import urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

IN_DIR   = "data/pasada1"
OUT_DIR  = "data/pasada2"
CKPT     = "data/checkpoint2.json"
NOMBRES  = "data/nombres_ordenados.json"

SHARD_N  = 50_000
WORKERS  = 16       # medido: 8 workers -> 15 paq/s con 0.4% error
PAUSA    = 0.03

os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "Accept": "application/vnd.npm.install-v1+json",
    "User-Agent": "UCN-research/1.0 (jairo.vergara@alumnos.ucn.cl)",
}

_parar = False
def _handler(sig, frame):
    global _parar
    if _parar:
        sys.exit(1)
    _parar = True
    print("\n  Ctrl+C recibido. Cerrando shard actual y guardando...")
signal.signal(signal.SIGINT, _handler)


def cargar_nombres():
    """Lista ordenada y cacheada. El orden fijo hace valido el checkpoint."""
    if os.path.exists(NOMBRES):
        return json.load(open(NOMBRES, encoding="utf-8"))
    print("Cargando nombres de la Pasada 1...")
    n = []
    for f in sorted(glob.glob(f"{IN_DIR}/*.jsonl")):
        for line in open(f, encoding="utf-8"):
            d = json.loads(line)
            if not d["deleted"]:
                n.append(d["id"])
    n.sort()
    json.dump(n, open(NOMBRES, "w", encoding="utf-8"))
    print(f"  {len(n):,} nombres guardados en {NOMBRES}")
    return n


def cargar_ckpt():
    if os.path.exists(CKPT):
        c = json.load(open(CKPT))
        c["inicio"] = time.time()
        c["base"]   = c["idx"]
        return c
    return {"idx": 0, "shard": 0, "ok": 0, "sin_version": 0,
            "error": 0, "inicio": time.time(), "base": 0}


def guardar_ckpt(c):
    tmp = CKPT + ".tmp"
    json.dump(c, open(tmp, "w"))
    os.replace(tmp, CKPT)


def pedir(nombre):
    url = "https://registry.npmjs.org/" + urllib.parse.quote(nombre, safe="@/")
    d = None
    for intento in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            break
        except Exception as e:
            if intento == 2:
                return {"name": nombre, "error": str(e)[:80]}
            time.sleep(1 + intento * 2)

    latest = (d.get("dist-tags") or {}).get("latest")
    vs = d.get("versions") or {}
    if not latest or latest not in vs:
        return {"name": nombre, "sin_version": True}

    v = vs[latest]
    return {
        "name":     nombre,
        "latest":   latest,
        "deps":     sorted((v.get("dependencies") or {}).keys()),
        "dev_deps": sorted((v.get("devDependencies") or {}).keys()),
        "tarball":  (v.get("dist") or {}).get("tarball"),
    }


def trabajo(nombre):
    time.sleep(PAUSA)
    return pedir(nombre)


def volcar(buffer, shard):
    ruta = f"{OUT_DIR}/shard_{shard:05d}.jsonl"
    tmp  = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for b in buffer:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")
    os.replace(tmp, ruta)      # atomico: el shard nunca queda a medias


def main():
    nombres = cargar_nombres()
    c = cargar_ckpt()
    total = len(nombres)

    print(f"\n{'='*56}")
    print(f"  Total a procesar : {total:,}")
    print(f"  Desde el indice  : {c['idx']:,}")
    print(f"  Restantes        : {total - c['idx']:,}")
    print(f"  Workers          : {WORKERS}")
    print(f"{'='*56}\n")

    if c["idx"] >= total:
        print("Ya esta completo.")
        return

    buffer = []
    shard  = c["shard"]
    pend   = nombres[c["idx"]:]

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i, res in enumerate(pool.map(trabajo, pend), start=1):
            buffer.append(res)
            if "error" in res:
                c["error"] += 1
            elif res.get("sin_version"):
                c["sin_version"] += 1
            else:
                c["ok"] += 1

            if len(buffer) >= SHARD_N or _parar:
                volcar(buffer, shard)
                shard   += 1
                c["shard"] = shard
                c["idx"]  += len(buffer)
                buffer = []
                guardar_ckpt(c)
                if _parar:
                    print(f"  Guardado en indice {c['idx']:,}. "
                          f"Vuelve a correr para continuar.")
                    return

            if i % 5_000 == 0:
                hechos = c["idx"] + len(buffer)
                pct    = hechos / total * 100
                seg    = time.time() - c["inicio"]
                vel    = i / seg
                falta  = (total - hechos) / vel / 3600
                print(f"  {hechos:>9,}/{total:,} | {pct:5.1f}% | "
                      f"ok={c['ok']:>9,} sv={c['sin_version']:>6,} "
                      f"err={c['error']:>6,} | {vel:5.1f}/s | "
                      f"faltan {falta:5.1f} h")

    if buffer:
        volcar(buffer, shard)
        c["shard"] = shard + 1
        c["idx"]  += len(buffer)
    guardar_ckpt(c)

    proc = c["ok"] + c["sin_version"] + c["error"]
    print(f"\n{'='*56}")
    print(f"  Con version   : {c['ok']:>12,}")
    print(f"  Sin version   : {c['sin_version']:>12,}")
    print(f"  Errores       : {c['error']:>12,}  "
          f"({c['error']/proc*100:.2f}%)" if proc else "")
    print(f"  Shards        : {c['shard']:>12,}")
    print(f"  Tiempo        : {(time.time()-c['inicio'])/3600:>12.1f} h")
    print(f"{'='*56}")


if __name__ == "__main__":
    main()