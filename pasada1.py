#!/usr/bin/env python3
"""
Pasada 1 -- Ingesta de identidad del registro npm.

Recorre el feed de replicacion y guarda: nombre, seq, estado (vivo/borrado).
No trae contenido: include_docs=true esta bloqueado por Cloudflare (400),
verificado el 18-09-2026 en cuatro variantes.

Salida : data/pasada1/shard_NNNNN.jsonl
Estado : data/checkpoint.json  (reanudable)
"""
import json, time, os
import urllib.request

TOPE    = 131_410_821          # tope medido 18-09-2026
LIMIT   = 10_000
OUT_DIR = "data/pasada1"
CKPT    = "data/checkpoint.json"
SHARD_N = 100_000

os.makedirs(OUT_DIR, exist_ok=True)


def cargar():
    if os.path.exists(CKPT):
        c = json.load(open(CKPT))
        c["inicio"] = time.time()      # reinicia el cronometro al reanudar
        return c
    return {"since": 0, "eventos": 0, "vivos": 0,
            "shard": 0, "paginas": 0, "inicio": time.time()}


def guardar(c):
    tmp = CKPT + ".tmp"
    json.dump(c, open(tmp, "w"))
    os.replace(tmp, CKPT)              # atomico


def pedir(since):
    url = (f"https://replicate.npmjs.com/registry/_changes"
           f"?limit={LIMIT}&since={since}")
    req = urllib.request.Request(url, headers={
        "User-Agent": "UCN-research/1.0 (jairo.vergara@alumnos.ucn.cl)"
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def volcar(buffer, shard):
    with open(f"{OUT_DIR}/shard_{shard:05d}.jsonl", "w", encoding="utf-8") as f:
        for b in buffer:
            f.write(json.dumps(b) + "\n")


def main():
    c = cargar()
    buffer = []
    shard  = c["shard"]

    if c["since"] > 0:
        print(f"Reanudando desde seq={c['since']:,}\n")
    else:
        print(f"Iniciando desde cero. Tope: {TOPE:,}\n")

    fallos = 0
    while c["since"] < TOPE:
        try:
            d = pedir(c["since"])
            fallos = 0
        except Exception as e:
            fallos += 1
            if fallos > 10:
                print(f"\n10 fallos seguidos. Abortando en seq={c['since']:,}")
                print("El checkpoint esta guardado, puedes reanudar despues.")
                break
            print(f"  error ({fallos}/10): {e} -- reintento en 5s")
            time.sleep(5)
            continue

        res = d.get("results", [])
        if not res:
            print("Feed agotado.")
            break

        for x in res:
            borrado = x.get("deleted", False)
            buffer.append({"id": x["id"], "seq": x["seq"], "deleted": borrado})
            if not borrado:
                c["vivos"] += 1

        c["since"]    = d["last_seq"]
        c["eventos"] += len(res)
        c["paginas"] += 1

        if len(buffer) >= SHARD_N:
            volcar(buffer, shard)
            shard += 1
            c["shard"] = shard
            buffer = []
            guardar(c)

        if c["paginas"] % 10 == 0:
            pct  = c["since"] / TOPE * 100
            mins = (time.time() - c["inicio"]) / 60
            print(f"  pag {c['paginas']:>5} | seq={c['since']:>12,} | "
                  f"{pct:5.1f}% | {c['eventos']:>9,} ev | "
                  f"{c['vivos']:>9,} vivos | {mins:5.1f} min")

        time.sleep(0.1)

    if buffer:
        volcar(buffer, shard)
        c["shard"] = shard + 1
    guardar(c)

    borr = c["eventos"] - c["vivos"]
    print(f"\n{'='*52}")
    print(f"  Eventos totales : {c['eventos']:>12,}")
    print(f"  Vivos           : {c['vivos']:>12,}")
    if c["eventos"]:
        print(f"  Borrados        : {borr:>12,}  ({borr/c['eventos']*100:.1f}%)")
    print(f"  Shards          : {c['shard']:>12,}")
    print(f"  Seq final       : {c['since']:>12,}")
    print(f"  Tiempo          : {(time.time()-c['inicio'])/60:>12.1f} min")
    print(f"{'='*52}")


if __name__ == "__main__":
    main()